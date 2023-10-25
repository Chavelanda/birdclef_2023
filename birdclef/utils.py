# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_utils.ipynb.

# %% auto 0
__all__ = ['DATA_DIR', 'AUDIO_DATA_DIR', 'plot_specgram', 'plot_waveform', 'plot_audio', 'mel_to_wave', 'plot_spectrogram',
           'plot_fbank']

# %% ../nbs/00_utils.ipynb 3
import matplotlib.pyplot as plt
import librosa
from pathlib import Path

import torch
import torchaudio

# %% ../nbs/00_utils.ipynb 4
DATA_DIR = '../data/'
AUDIO_DATA_DIR = DATA_DIR + 'audio_data/'

# %% ../nbs/00_utils.ipynb 5
def plot_specgram(waveform:torch.Tensor, # The tensor containing the waveform
                  sample_rate:int,  # The sample rate of the audio file 
                  title:str="Spectrogram", # The title of the plot
                  axes=None):
    "A function to plot the specgram from a waveform"
    waveform = waveform.numpy()

    num_channels, num_frames = waveform.shape

    plot = False
    if axes is None:
      plot = True
      figure, axes = plt.subplots(num_channels, 1)

    if num_channels == 1:
        axes = [axes]
    for c in range(num_channels):
        axes[c].specgram(waveform[c], Fs=sample_rate)
        axes[c].title.set_text(title + f' Channel {c+1}')
        if num_channels > 1:
            axes[c].set_ylabel(f"Channel {c+1}")

    if plot:
      plt.show(block=False)

# %% ../nbs/00_utils.ipynb 6
def plot_waveform(waveform:torch.Tensor, # The tensor containing the waveform
                  sample_rate:int, # The sample rate of the audio file
                  title:str='Waveform', # The title of the plot
                  axes=None):
    "A function to plot the waveform of an audio"
    waveform = waveform.numpy()

    num_channels, num_frames = waveform.shape
    time_axis = torch.arange(0, num_frames) / sample_rate

    plot = False
    if axes is None:
        plot = True
        figure, axes = plt.subplots(num_channels, 1)

    if num_channels == 1:
        axes = [axes]
    for c in range(num_channels):
        axes[c].plot(time_axis, waveform[c], linewidth=1)
        axes[c].grid(True)
        axes[c].title.set_text(title + f' Channel {c+1}')
        if num_channels > 1:
            axes[c].set_ylabel(f"Channel {c+1}")

    if plot:
        plt.show(block=False)

# %% ../nbs/00_utils.ipynb 7
def plot_audio(waveform:torch.Tensor, # The tensor containing the waveform
                sample_rate:int): # The sample rate of the audio file
    "A function that plots together the waveform and the specgram of an audio."
    num_channels, num_frames = waveform.numpy().shape

    figure, axes = plt.subplots(num_channels, 2,  figsize=(16, num_channels * 7))

    if num_channels == 1:
        axes_w = axes[0]
        axes_s = axes[1]
    else:
        axes_w = axes[:, 0]
        axes_s = axes[:, 1]

    plot_waveform(waveform, sample_rate, axes=axes_w)
    plot_specgram(waveform, sample_rate, axes=axes_s)

    plt.show(block=False)

# %% ../nbs/00_utils.ipynb 8
def mel_to_wave(mel_specgram:torch.Tensor, # The tensor of the mel specgram
                sample_rate:int = 32000,  # The sample rate of the audio
                n_fft:int=2048
                )->torch.Tensor: # The tensor of the waveform
    "Function used to recover a waveform from a mel spectrogram"
    n_stft = int((n_fft//2) + 1)
    mel_specgram = mel_specgram.cpu()
    mel_specgram = torch.pow(10, mel_specgram/10)
    invers_transform = torchaudio.transforms.InverseMelScale(sample_rate=sample_rate, n_stft=n_stft)
    grifflim_transform = torchaudio.transforms.GriffinLim(n_fft=n_fft)

    inverse_waveform = invers_transform(mel_specgram)
    pseudo_waveform = grifflim_transform(inverse_waveform)

    return pseudo_waveform

# %% ../nbs/00_utils.ipynb 9
def plot_spectrogram(specgram, title=None, ylabel="freq_bin", ax=None, db=False):
    if ax is None:
        _, ax = plt.subplots(1, 1)
    if title is not None:
        ax.set_title(title)
    ax.set_ylabel(ylabel)
    if not db:
        specgram = librosa.power_to_db(specgram)
    ax.imshow(specgram, origin="lower", aspect="auto", interpolation="nearest")
    plt.show()


def plot_fbank(fbank, title=None):
    fig, axs = plt.subplots(1, 1)
    axs.set_title(title or "Filter bank")
    axs.imshow(fbank, aspect="auto")
    axs.set_ylabel("frequency bin")
    axs.set_xlabel("mel bin")
