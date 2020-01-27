#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 24.01.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------


import os,os.path,logging
import numpy as np
import matplotlib.pyplot as pl
from   matplotlib.backends.backend_pdf import PdfPages

import mne
from jumeg.base.jumeg_base import JuMEG_Base_IO

logger = logging.getLogger('jumeg')
__version__="2020.01.24.001"


#--- A4 landscape
pl.rc('figure', figsize=(11.69,8.27))
pl.rcParams.update({'font.size': 8})



class JuMEG_ICA_PERFORMANCE_PLOT(object):
    """
     from jumeg.base.pipelies.jumeg_base_pipelines_plot import JuMEG_ICA_PERFORMANCE_PLOT
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._init(**kwargs)

    def _init(self):
        self._figs   = []
        self._n_figs = None
    
        
    def init(self,**kwargs):
        try:
           plt.clear('all')
        except:
           pass
        self._figs = []

    def plot(self,raw=None,raw_cleaned=None,picks=None,ref_picks=None):
      #--- init fig
        fig=None
       

        self._figs.append(fig)

        return fig
'''


def plot_performance_artifact_rejection(meg_raw, ica, fnout_fig,
                                        meg_clean=None, show=False,
                                        proj=False, verbose=False,
                                        name_ecg='ECG 001', name_eog='EOG 002'):
    
    Creates a performance image of the data before
    and after the cleaning process.
   

    import matplotlib.pyplot as pl
    from mne.preprocessing import find_ecg_events, find_eog_events
    from jumeg import jumeg_math as jmath

    # name_ecg = 'ECG 001'
    # name_eog_hor = 'EOG 001'
    # name_eog_ver = 'EOG 002'
    event_id_ecg = 999
    event_id_eog = 998
    tmin_ecg = -0.4
    tmax_ecg = 0.4
    tmin_eog = -0.4
    tmax_eog = 0.4

    picks = mne.pick_types(meg_raw.info, meg=True, ref_meg=False,
                           exclude='bads')
    # as we defined x% of the explained variance as noise (e.g. 5%)
    # we will remove this noise from the data
    if meg_clean:
        meg_clean_given = True
    else:
        meg_clean_given = False
        meg_clean = ica.apply(meg_raw.copy(), exclude=ica.exclude,
                              n_pca_components=ica.n_components_)

    # plotting parameter
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    # check if ECG and EOG was recorded in addition
    # to the MEG data
    ch_names = meg_raw.info['ch_names']

    # ECG
    if name_ecg in ch_names:
        nstart = 0
        nrange = 1
    else:
        nstart = 1
        nrange = 1

    # EOG
    if name_eog in ch_names:
        nrange = 2

    y_figsize = 6 * nrange
    perf_art_rej = np.zeros(2)

    # ToDo:  How can we avoid popping up the window if show=False ?
    pl.ioff()
    pl.figure('performance image', figsize=(12, y_figsize))
    pl.clf()

    # ECG, EOG:  loop over all artifact events
    for i in range(nstart, nrange):
        # get event indices
        if i == 0:
            baseline = (None, None)
            event_id = event_id_ecg
            idx_event, _, _ = find_ecg_events(meg_raw, event_id,
                                              ch_name=name_ecg,
                                              verbose=verbose)
            idx_ref_chan = meg_raw.ch_names.index(name_ecg)
            tmin = tmin_ecg
            tmax = tmax_ecg
            pl1 = nrange * 100 + 21
            pl2 = nrange * 100 + 22
            text1 = "CA: original data"
            text2 = "CA: cleaned data"
        elif i == 1:
            baseline = (None, None)
            event_id = event_id_eog
            idx_event = find_eog_events(meg_raw, event_id, ch_name=name_eog,
                                        verbose=verbose)
            idx_ref_chan = meg_raw.ch_names.index(name_eog)
            tmin = tmin_eog
            tmax = tmax_eog
            pl1 = nrange * 100 + 21 + (nrange - nstart - 1) * 2
            pl2 = nrange * 100 + 22 + (nrange - nstart - 1) * 2
            text1 = "OA: original data"
            text2 = "OA: cleaned data"

        # average the signals
        raw_epochs = mne.Epochs(meg_raw, idx_event, event_id, tmin, tmax,
                                picks=picks, baseline=baseline, proj=proj,
                                verbose=verbose)
        cleaned_epochs = mne.Epochs(meg_clean, idx_event, event_id, tmin, tmax,
                                    picks=picks, baseline=baseline, proj=proj,
                                    verbose=verbose)
        ref_epochs = mne.Epochs(meg_raw, idx_event, event_id, tmin, tmax,
                                picks=[idx_ref_chan], baseline=baseline,
                                proj=proj, verbose=verbose)

        raw_epochs_avg = raw_epochs.average()
        cleaned_epochs_avg = cleaned_epochs.average()
        ref_epochs_avg = np.average(ref_epochs.get_data(), axis=0).flatten() * -1.0
        times = raw_epochs_avg.times * 1e3
        if np.max(raw_epochs_avg.data) < 1:
            factor = 1e15
        else:
            factor = 1
        ymin = np.min(raw_epochs_avg.data) * factor
        ymax = np.max(raw_epochs_avg.data) * factor

        # plotting data before cleaning
        pl.subplot(pl1)
        pl.plot(times, raw_epochs_avg.data.T * factor, 'k')
        pl.title(text1)
        # plotting reference signal
        pl.plot(times, jmath.rescale(ref_epochs_avg, ymin, ymax), 'r')
        pl.xlim(times[0], times[len(times) - 1])
        pl.ylim(1.1 * ymin, 1.1 * ymax)
        # print some info
        textstr1 = 'num_events=%d\nEpochs: tmin, tmax = %0.1f, %0.1f' \
                   % (len(idx_event), tmin, tmax)
        pl.text(times[10], 1.09 * ymax, textstr1, fontsize=10,
                verticalalignment='top', bbox=props)

        # plotting data after cleaning
        pl.subplot(pl2)
        pl.plot(times, cleaned_epochs_avg.data.T * factor, 'k')
        pl.title(text2)
        # plotting reference signal again
        pl.plot(times, jmath.rescale(ref_epochs_avg, ymin, ymax), 'r')
        pl.xlim(times[0], times[len(times) - 1])
        pl.ylim(1.1 * ymin, 1.1 * ymax)
        # print some info
        perf_art_rej[i] = calc_performance(raw_epochs_avg, cleaned_epochs_avg)
        # ToDo: would be nice to add info about ica.excluded
        if meg_clean_given:
            textstr1 = 'Performance: %d\nFrequency Correlation: %d'\
                       % (perf_art_rej[i],
                          calc_frequency_correlation(raw_epochs_avg, cleaned_epochs_avg))
        else:
            textstr1 = 'Performance: %d\nFrequency Correlation: %d\n# ICs: %d\nExplained Var.: %d'\
                       % (perf_art_rej[i],
                          calc_frequency_correlation(raw_epochs_avg, cleaned_epochs_avg),
                          ica.n_components_, ica.n_components * 100)

        pl.text(times[10], 1.09 * ymax, textstr1, fontsize=10,
                verticalalignment='top', bbox=props)

    if show:
        pl.show()

    # save image
    pl.savefig(fnout_fig + '.png', format='png')
    pl.close('performance image')
    pl.ion()

    return perf_art_rej


'''