# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_network.ipynb.

# %% auto 0
__all__ = ['model_dict', 'EfficientNetV2', 'get_model']

# %% ../nbs/03_network.ipynb 3
from typing import Union, BinaryIO, IO
from os import PathLike

import torch
import torchvision
from torch.nn import Module

from .dataset import get_dataloader


# %% ../nbs/03_network.ipynb 5
class EfficientNetV2(torch.nn.Module):
    def __init__(self, num_classes=264, size='s'):
        super().__init__()

        if size=='s':
            self.efficientnet_v2 = torchvision.models.efficientnet_v2_s(weights=None, progress=True, num_classes=num_classes)
        elif size=='m':
            self.efficientnet_v2 = torchvision.models.efficientnet_v2_m(weights=None, progress=True, num_classes=num_classes)
        else:
            self.efficientnet_v2 = torchvision.models.efficientnet_v2_l(weights=None, progress=True, num_classes=num_classes)

        self.init_conv = torch.nn.Conv2d(1, 3, (3,3), padding="same")
        #self.sigmoid = torch.nn.functional.sigmoid

    def forward(self, x):
        x = self.init_conv(x)
        x = self.efficientnet_v2(x)

        return x

# %% ../nbs/03_network.ipynb 10
model_dict = {
        'efficient_net_v2_s': (EfficientNetV2, {})
        }

def get_model(model_key:str, # A key of the model dictionary
              weights_path:Union[str, PathLike, BinaryIO, IO[bytes]] = None,   # A file-like object to the model weights
              num_classes:int = 264,  # Number of classes to predict
              )->Module:      # A pytorch model
    "A getter method to retrieve the wanted (possibly pretrained) model"
    assert model_key in model_dict, f'{model_key} is not an existing network, choose one from {model_dict.keys()}.'
    
    net_class, kwargs = model_dict[model_key]
    model = net_class(num_classes=num_classes, **kwargs)

    if weights_path is not None:
        model.load_state_dict(torch.load(weights_path))

    return model
