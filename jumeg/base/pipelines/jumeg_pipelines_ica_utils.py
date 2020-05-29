#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 26.05.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------


import os,os.path as op
import numpy as np
import time,datetime

from distutils.dir_util import mkpath

import mne

#from jumeg.decompose.ica_replace_mean_std import ICA,apply_ica_replace_mean_std
from mne.preprocessing import ICA
from mne.preprocessing import ctps_ as ctps
#from jumeg.jumeg_preprocessing            import get_ics_cardiac, get_ics_ocular
#---
from jumeg.base import jumeg_logger
from jumeg.base.jumeg_base import jumeg_base as jb
from jumeg.base.jumeg_base_config import JuMEG_CONFIG as jCFG
#---
#from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance import JuMEG_ICA_PERFORMANCE
#from jumeg.base.pipelines.jumeg_pipelines_ica_svm import JuMEG_ICA_SVM
#from jumeg.base.pipelines.jumeg_pipelines_chopper import JuMEG_PIPELINES_CHOPPER

#---
# from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER

logger = jumeg_logger.get_logger()

__version__ = "2020.05.28.001"


#######################################################
#
#  determine occular related ICs
#  jumeg.jumeg_preprocessing
#######################################################
def get_ics_ocular(meg_raw,ica,flow=1,fhigh=10,
                   name_eog_hor='EOG 001',name_eog_ver='EOG 002',
                   score_func='pearsonr',thresh=0.3):
    '''
    Find Independent Components related to ocular artefacts
    '''
    
    # Note: when using the following:
    #   - the filter settings are different
    #   - here we cannot define the filter range
    
    # vertical EOG
    # idx_eog_ver = [meg_raw.ch_names.index(name_eog_ver)]
    # eog_scores = ica.score_sources(meg_raw, meg_raw[idx_eog_ver][0])
    # eogv_idx = np.where(np.abs(eog_scores) > thresh)[0]
    # ica.exclude += list(eogv_idx)
    # ica.plot_topomap(eog_idx)
    
    # horizontal EOG
    # idx_eog_hor = [meg_raw.ch_names.index(name_eog_hor)]
    # eog_scores = ica.score_sources(meg_raw, meg_raw[idx_eog_hor][0])
    # eogh_idx = np.where(np.abs(eog_scores) > thresh)[0]
    # ica.exclude += list(eogh_idx)
    # ica.plot_topomap(eog_idx)
    # print [eogv_idx, eogh_idx]
    
    # vertical EOG
    if name_eog_ver in meg_raw.ch_names:
        idx_eog_ver = [meg_raw.ch_names.index(name_eog_ver)]
        eog_ver_filtered = mne.filter.filter_data(meg_raw[idx_eog_ver,:][0],
                                                  meg_raw.info['sfreq'],
                                                  l_freq=flow,h_freq=fhigh)
        eog_ver_scores = ica.score_sources(meg_raw,target=eog_ver_filtered,
                                           score_func=score_func)
        # plus 1 for any()
        ic_eog_ver = np.where(np.abs(eog_ver_scores) >= thresh)[0] + 1
        if not ic_eog_ver.any():
            ic_eog_ver = np.array([0])
    else:
        logger.warning(">>>> NOTE: No vertical EOG channel found!")
        ic_eog_ver = np.array([0])
    
    # horizontal EOG
    if name_eog_hor in meg_raw.ch_names:
        idx_eog_hor = [meg_raw.ch_names.index(name_eog_hor)]
        eog_hor_filtered = mne.filter.filter_data(meg_raw[idx_eog_hor,:][0],
                                                  meg_raw.info['sfreq'],
                                                  l_freq=flow,h_freq=fhigh)
        eog_hor_scores = ica.score_sources(meg_raw,target=eog_hor_filtered,
                                           score_func=score_func)
        # plus 1 for any()
        ic_eog_hor = np.where(np.abs(eog_hor_scores) >= thresh)[0] + 1
        if not ic_eog_hor.any():
            ic_eog_hor = np.array([0])
    else:
        logger.warning(">>>> NOTE: No horizontal EOG channel found!")
        ic_eog_hor = np.array([0])
    
    # combine both
    idx_eog = []
    for i in range(ic_eog_ver.size):
        ix = ic_eog_ver[i] - 1
        if (ix >= 0):
            idx_eog.append(ix)
    for i in range(ic_eog_hor.size):
        ix = ic_eog_hor[i] - 1
        if (ix >= 0):
            idx_eog.append(ix)
    
    return idx_eog


#######################################################
#
#  determine cardiac related ICs
#  jumeg.jumeg_preprocessing
#######################################################
def get_ics_cardiac(meg_raw,ica,flow=10,fhigh=20,tmin=-0.3,tmax=0.3,
                    name_ecg='ECG 001',use_CTPS=True,proj=False,
                    score_func='pearsonr',thresh=0.3):
    '''
    Identify components with cardiac artefacts

    ToDo mk CLS use annotations
    anno_evt,anno_labels = mne.events_from_annotations(self.raw)
    idx = np.where(raw.annotations.description == description)[0]
    msg.extend([
                       " --> mne.annotations in RAW:\n  -> {}".format(raw.annotations),
                       "-"*40,
                       "  -> <{}> onsets:\n{}".format(description,raw.annotations.onset[idx]),
                       "-"*40])

           logger.info("\n".join(msg))
    idx_R_peak = ecg onsets
    '''
    
    from mne.preprocessing import find_ecg_events
    event_id_ecg = 999
    
    if name_ecg in meg_raw.ch_names:
        # get and filter ICA signals
        ica_raw = ica.get_sources(meg_raw)
        ica_raw.filter(l_freq=flow,h_freq=fhigh,n_jobs=2,method='fft')
        # get R-peak indices in ECG signal
        idx_R_peak,_,_ = find_ecg_events(meg_raw,ch_name=name_ecg,
                                         event_id=event_id_ecg,l_freq=flow,
                                         h_freq=fhigh,verbose=False)
        
        # -----------------------------------
        # default method:  CTPS
        #           else:  correlation
        # -----------------------------------
        if use_CTPS:
            # create epochs
            picks = np.arange(ica.n_components_)
            ica_epochs = mne.Epochs(ica_raw,events=idx_R_peak,
                                    event_id=event_id_ecg,tmin=tmin,
                                    tmax=tmax,baseline=None,
                                    proj=False,picks=picks,verbose=False)
            # compute CTPS
            _,pk,_ = ctps.ctps(ica_epochs.get_data())
            
            pk_max = np.max(pk,axis=1)
            ecg_scores = pk_max
            idx_ecg = np.where(pk_max >= thresh)[0]
        else:
            # use correlation
            idx_ecg = [meg_raw.ch_names.index(name_ecg)]
            ecg_filtered = mne.filter.filter_data(meg_raw[idx_ecg,:][0],
                                                  meg_raw.info['sfreq'],
                                                  l_freq=flow,h_freq=fhigh)
            ecg_scores = ica.score_sources(meg_raw,target=ecg_filtered,
                                           score_func=score_func)
            idx_ecg = np.where(np.abs(ecg_scores) >= thresh)[0]
    
    else:
        logger(">>>> NOTE: No ECG channel found!")
        idx_ecg = np.array([0])
    
    return idx_ecg,ecg_scores


def fit_ica(raw,picks,reject,ecg_ch,eog_hor,eog_ver,
            flow_ecg,fhigh_ecg,flow_eog,fhigh_eog,ecg_thresh,
            eog_thresh,use_jumeg=True,random_state=42):
    """
    author: C.Kiefer; c.kiefer@fz-juelich.de

    Fit an ICA object to the raw file. Identify cardiac and ocular components
    and mark them for removal.

    Parameters:
    -----------
    inst : instance of Raw, Epochs or Evoked
        Raw measurements to be decomposed.
    picks : array-like of int
        Channels to be included. This selection remains throughout the
        initialized ICA solution. If None only good data channels are used.
    reject : dict | None
        Rejection parameters based on peak-to-peak amplitude.
        Valid keys are 'grad', 'mag', 'eeg', 'seeg', 'ecog', 'eog', 'ecg',
        'hbo', 'hbr'.
        If reject is None then no rejection is done. Example::

            reject = dict(grad=4000e-13, # T / m (gradiometers)
                          mag=4e-12, # T (magnetometers)
                          eeg=40e-6, # V (EEG channels)
                          eog=250e-6 # V (EOG channels)
                          )

        It only applies if `inst` is of type Raw.
    ecg_ch : array-like | ch_name | None
        ECG channel to which the sources shall be compared. It has to be
        of the same shape as the sources. If some string is supplied, a
        routine will try to find a matching channel. If None, a score
        function expecting only one input-array argument must be used,
        for instance, scipy.stats.skew (default).
    eog_hor : array-like | ch_name | None
        Horizontal EOG channel to which the sources shall be compared.
        It has to be of the same shape as the sources. If some string
        is supplied, a routine will try to find a matching channel. If
        None, a score function expecting only one input-array argument
        must be used, for instance, scipy.stats.skew (default).
    eog_ver : array-like | ch_name | None
        Vertical EOG channel to which the sources shall be compared.
        It has to be of the same shape as the sources. If some string
        is supplied, a routine will try to find a matching channel. If
        None, a score function expecting only one input-array argument
        must be used, for instance, scipy.stats.skew (default).
    flow_ecg : float
        Low pass frequency for ECG component identification.
    fhigh_ecg : float
        High pass frequency for ECG component identification.
    flow_eog : float
        Low pass frequency for EOG component identification.
    fhigh_eog : float
        High pass frequency for EOG component identification.
    ecg_thresh : float
        Threshold for ECG component idenfication.
    eog_thresh : float
        Threshold for EOG component idenfication.
    use_jumeg : bool
        Use the JuMEG scoring method for the identification of
        artifact components.
    random_state : None | int | instance of np.random.RandomState
        np.random.RandomState to initialize the FastICA estimation.
        As the estimation is non-deterministic it can be useful to
        fix the seed to have reproducible results. Defaults to None.

    Returns:
    --------
    ica : mne.preprocessing.ICA
        ICA object for raw file with ECG and EOG components marked for removal.

    """
    # increased iteration to make it converge
    # fix the number of components to 40, depending on your application you
    # might want to raise the number
    # 'extended-infomax', 'fastica', 'picard'
    
    logger.info('Start ICA FIT: init ICA object')
    ica = ICA(method='fastica',n_components=40,random_state=random_state,
              max_pca_components=None,max_iter=5000,verbose=False)
    
    logger.debug('ICA FIT: apply ICA.fit\n reject: {} \n picks: {}'.format(reject,picks))
    ica.fit(raw,picks=picks,decim=None,reject=reject,verbose=True)
    logger.info('Done ICA FIT')
    
    #######################################################################
    # identify bad components
    #######################################################################
    
    ica.exclude = []
    
    if use_jumeg:
        logger.info("JuMEG Computing scores and identifying components ...")
        #--- get ECG related components using JuMEG
        '''
        ToDO use annotations to events
        get_ics_cardiac_from_annotations
        '''
        ic_ecg,sc_ecg = get_ics_cardiac(raw,ica,flow=flow_ecg,fhigh=fhigh_ecg,
                                        thresh=ecg_thresh,tmin=-0.5,tmax=0.5,name_ecg=ecg_ch,
                                        use_CTPS=True)  #[0]
        ica.exclude.extend(ic_ecg)
        #--- get EOG related components using JuMEG
        '''
        ToDO use annotations to events
        get_ics_ocular_from_annotations
        '''
        ic_eog = get_ics_ocular(raw,ica,flow=flow_eog,fhigh=fhigh_eog,
                                thresh=eog_thresh,name_eog_hor=eog_hor,name_eog_ver=eog_ver,
                                score_func='pearsonr')
        #--- if necessary include components identified by correlation as well
        ica.exclude.extend(ic_eog)
        
        msg = ["JuMEG identified ICA components",
               "  -> ECG components: {}".format(ic_ecg),
               "  ->         scores: {}".format(sc_ecg[ic_ecg]),
               "  -> EOG components: {}".format(ic_eog)
               ]
        logger.debug("\n".join(msg))
    else:
        logger.info("MNE Computing scores and identifying components ...")
        ecg_scores = ica.score_sources(raw,target=ecg_ch,score_func='pearsonr',
                                       l_freq=flow_ecg,h_freq=fhigh_ecg,verbose=False)
        # horizontal channel
        eog1_scores = ica.score_sources(raw,target=eog_hor,score_func='pearsonr',
                                        l_freq=flow_eog,h_freq=fhigh_eog,verbose=False)
        # vertical channel
        eog2_scores = ica.score_sources(raw,target=eog_ver,score_func='pearsonr',
                                        l_freq=flow_eog,h_freq=fhigh_eog,verbose=False)
        
        # print the top ecg, eog correlation scores
        ecg_inds = np.where(np.abs(ecg_scores) > ecg_thresh)[0]
        eog1_inds = np.where(np.abs(eog1_scores) > eog_thresh)[0]
        eog2_inds = np.where(np.abs(eog2_scores) > eog_thresh)[0]
        
        highly_corr = np.concatenate((ecg_inds,eog1_inds,eog2_inds))
        highly_corr_ecg = list(set(ecg_inds))
        highly_corr_eog1 = list(set(eog1_inds))
        highly_corr_eog2 = list(set(eog2_inds))
        
        highly_corr_ecg.sort()
        highly_corr_eog1.sort()
        highly_corr_eog2.sort()
        
        # if necessary include components identified by correlation as well
        ica.exclude = highly_corr
        msg = ["MNE Highly correlated artifact components",
               "  -> ECG  : {} ".format(highly_corr_ecg),
               "  -> EOG 1: {} ".format(highly_corr_eog1),
               "  -> EOG 2: {} ".format(highly_corr_eog2)
               ]
        
        logger.debug("\n".join(msg))
        ica.exclude.extend(highly_corr)
    
    ica.exclude = list(set(ica.exclude))
    ica.exclude.sort()
    logger.info("done ICA FIT\n  -> excluded ICs: {}\n".format(ica.exclude))
    return ica


def ica_artefact_rejection_and_apply(raw,ica_obj,picks=None,reject=None,copy_raw=True): #,copy_ica=True
    """
    Applies ICA to the raw object. (ica transform)

    Parameters
    ----------
        raw : mne.io.Raw()  (raw chop)
                 Raw object ICA is applied to
        ica : ICA object
              ICA object being applied d to the raw object
        picks: picks, <None>
        reject: MNE reject dict

        copy_raw: make a copy of raw
  
    Returns
    -------
        raw_clean : mne.io.Raw()
                   Raw object after ICA cleaning
        ica obj, copy &   replace mean,std
    """
    logger.info("Start ICA Transform => call <ica.apply> and replace mean & std")
    
    if picks is None:
        picks = jb.picks.meg_nobads(raw)
    
    if copy_raw:
       _raw = raw.copy()
    else:
       _raw = raw
    
    #if copy_ica:
    #ica = ICA.copy()  # ToDo exclude copy
    #else:
    # ica = ICA
      
    # compute pre-whitener and PCA data mean
    # ToDo ck if copy and get_data doubled copy
    data       = _raw.get_data(picks)  #, None, None, None)
    pre_whiten = np.atleast_2d(np.ones(len(picks)) * data.std()).T
    data,_     = ica_obj._pre_whiten(data,_raw.info,picks)  # works inplace
    pca_mean_  = np.mean(data,axis=1)
    
    # apply ICA
    ica_obj.pca_mean_     = pca_mean_
    ica_obj._pre_whitener = pre_whiten
    return ica_obj.apply(_raw)  # raw_clean
