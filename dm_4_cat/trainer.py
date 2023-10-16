# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_trainer.ipynb.

# %% auto 0
__all__ = ['log_weights', 'train_one_epoch', 'validate_model', 'train']

# %% ../nbs/04_trainer.ipynb 3
import math
import copy
from tqdm.notebook import tqdm

import wandb
import torch

from .dataset import get_dataloader
from .network import get_model
from .training_utils import get_optimizer, get_loss_func, compute_metrics

# %% ../nbs/04_trainer.ipynb 4
def log_weights(model, # A pytorch model
                artifact_name, # The name of the artifact
                config # wandb config
                ):
    "A method to log artifacts into wandb"

    model_artifact = wandb.Artifact(
        artifact_name, type="model",
        metadata=dict(config))

    torch.save(model.state_dict(), f"{artifact_name}.pth")
    
    model_artifact.add_file(f"{artifact_name}.pth")

    wandb.log_artifact(model_artifact)

# %% ../nbs/04_trainer.ipynb 5
def train_one_epoch(model,                  # A pytorch model
                    train_dl,               # A pytorch dataloader
                    loss_func,              # A function to compute the loss
                    optimizer,              # The optimizer
                    device,                 # The device where the training is executed ('cpu'|'cuda')
                    epoch,                  # The epoch the model is training
                    example_ct,             # The number of examples the model has been trained on
                    step_ct,                # The number of backpropagation steps the model has done
                    n_steps_per_epoch,      # The number of steps for each epoch
                    ):
    "Train a pytorch model for one epoch"

    model.train()
    progress_bar = tqdm(range(len(train_dl)))

    for step, (inputs, labels) in enumerate(train_dl):
        inputs, labels = inputs.to(device), labels.to(device)

        outputs = model(inputs)

        train_loss = loss_func(outputs, labels)
        optimizer.zero_grad()
        train_loss.backward()
        optimizer.step()

        example_ct += len(input)

        epoch_number = (step + 1) / n_steps_per_epoch + epoch
        metrics = compute_metrics('train', outputs, labels, train_loss, example_ct, step_ct, epoch_number)

        if (step + 1) < n_steps_per_epoch:
            # Log train metrics to wandb
            wandb.log(metrics)

        step_ct += 1
        progress_bar.update(1)

    return metrics, example_ct, step_ct

# %% ../nbs/04_trainer.ipynb 6
def validate_model(model, # A pytorch model
                   valid_dl, # A pytorch dataloader
                   loss_func, # The loss function
                   device, # The device where the training is executed ('cpu'|'cuda')
                   epoch, # The epoch the model has been trained
                   example_ct, # The number of examples the model has been trained on
                   step_ct, # The number of backpropagation steps the model has done
                   dataset_type='val' # The name of the dataset used
                  ):
    "Test or validate a pytorch model"
    
    model.eval()
    
    metrics = {}
    labels_acc = []
    outputs_acc = []
    loss = 0.0
    
    progress_bar = tqdm(range(len(valid_dl)))
    with torch.inference_mode():
        for i, (inputs, labels) in enumerate(valid_dl):

            inputs, labels = inputs.to(device), labels.to(device)

            # Forward pass
            outputs = model(inputs)
            loss += loss_func(outputs, labels) * labels.size(0)

            # Add labels and outputs to acc
            labels_acc.append(labels)
            outputs_acc.append(outputs)

            progress_bar.update(1)

    # Divide loss by dataset length
    val_loss = loss / len(valid_dl.dataset)

    labels = torch.cat(labels_acc, dim=0)
    outputs = torch.cat(outputs_acc, dim=0)

    metrics = compute_metrics(dataset_type, outputs, labels, val_loss, example_ct, step_ct, epoch)

    return metrics

# %% ../nbs/04_trainer.ipynb 7
def train(conf = None # Wandb configurations containing all hyperparameters
          ):
    "Train, validate and test a model using the given configurations"

    with wandb.init(conf) as run:
        config = wandb.config
        run.name = f"{config.run_name}"

        # Getting dataloaders
        train_dl = get_dataloader(config.train_key, **config.train_kwargs)
        valid_dl = get_dataloader(config.val_key, **config.val_kwargs)
        test_dl = get_dataloader(config.test_key, **config.val_kwargs)

        # Getting model, optimizer and loss function
        model = get_model(config.model_key, **config.model_kwargs)
        model.to(config.device)
        optimizer = get_optimizer(config.optimizer_key, **config.optimizer_kwargs)
        loss_func = get_loss_func(config.loss_key)

        n_steps_per_epoch = math.ceil(len(train_dl.dataset) / config.train_kwargs.batch_size)

        # Counters
        example_ct = 0
        step_ct = 0

        best_val = -1
        for epoch in range(config.epochs):
            print(f"Training epoch {epoch}")
            # Train
            metrics, example_ct, step_ct = train_one_epoch(model, train_dl, loss_func, optimizer, config.device, epoch, example_ct, step_ct, n_steps_per_epoch)

            print("\tFinished training. Starting validation")

            # Validate
            val_metrics = validate_model(model, valid_dl, loss_func, config.device, epoch + 1, example_ct, step_ct)

            print('\tFinshed validation')

            # Log train and validation metrics to wandb
            wandb.log({**metrics, **val_metrics})

            print("\tMetrics logged to wandb")

            # If the best metric is reached, save the artifact
            if val_metrics[f'val/{config.metric}'] > best_val:
                print(f'\t{config.metric} in the validation set has improved!')
                best_val = val_metrics[f'val/{config.metric}']
                best_example, best_step, best_epoch = example_ct, step_ct, epoch
                best_model = copy.deepcopy(model)
                log_weights(model, config.run_name, config)

        print("\tTesting with best model")
        # Test best model
        test_metrics = validate_model(best_model, test_dl, loss_func, config.device, best_epoch, best_example, best_step, dataset_type="test")

        # Load test metrics as summary
        for key in test_metrics.keys():
            wandb.summary[key] = test_metrics[key]