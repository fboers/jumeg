#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 05.06.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import numpy as np
import matplotlib.pyplot as plt

import mne
from mne import io, read_proj, read_selection
from mne.datasets import sample
from mne.time_frequency import psd_multitaper

from jumeg.base.jumeg_base import jumeg_base as jb

fraw="/media/fboers/USB_2TB/exp/MEG94TSCH/mne/205386/MEG94T/120906_1404/1/205386_MEG94T_120906_1404_1_reraw_c,rfDC,n-raw.fif"

fmin=0.0
fmax=20.0
n_fft=4096

raw,fname= jb.get_raw_obj(fraw,raw=None)
raw.plot_psd(area_mode='range',  fmin=fmin, fmax=fmax, n_fft=n_fft, show=True, average=True)