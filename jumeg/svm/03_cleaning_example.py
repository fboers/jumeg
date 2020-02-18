# -*- coding: utf-8 -*-
"""
Spyder Edi*tor

This is a temporary script file.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 13:12:26 2020
@author: nkampel
"""

import os
import numpy as np
import mne
import pickle

def get_ica_artifacts_compatible(raw,
                                 modelfile,
                                 systemtype = '4d', #(4d, nmag, ctf)
                                 thres = 0.8,  
                                 n_components=30,
                                 tmin = 0.,
                                 tmax = None,
                                 sfreq = 250,
                                 n_jobs = 6,
                                 l_freq=2.,
                                 h_freq=50,
                                 method='fastica'):
    u"""Artifact removal using the mne ICA-decomposition
    for common MEG systems (neuromag, ctf, 4d).
    Artifactual components are being indentified by a support vector
    machine. Model trained on a 4d dataset composed on 48 Subjects.
    
    Compatibility to ctf and neuromag systems is established via
    3d interpolation of the
    magnetometer sensordata to the  4d system

    Parameters
    ----------
    raw : .fif
        a raw .fif file
    modelfile :  object
        an skit-learn classifier object 'download from jumeg...'
    systemtype : str
        the system type of the raw file (4d, nmag, ctf)
    thres : float (from 0. to 1.)
        higher is less sensitive to artifact components,
        lower is more sensitive to artifact components,
        defaults to 0.8.  
    ica_parameters:
        standard parameters for the mne ica function

    """
    #load SVM-Model
    all_models = pickle.load( open( modelfile, "rb" ) )
    classifier = all_models[systemtype]
    # we are fitting the ica on filtered copy of the original
    raw_c = raw.copy().crop(tmin=tmin, tmax=tmax)
    raw_c.resample(sfreq=sfreq,n_jobs=n_jobs)
    raw_c.interpolate_bads() # to get the dimesions right
    raw_c.filter(l_freq=l_freq, h_freq=h_freq)
    picks = mne.pick_types(raw_c.info, meg='mag',ref_meg=False)
    ica = mne.preprocessing.ICA(n_components=n_components, method=method)
    ica.fit(raw_c, picks= picks)# ,start=0.0,stop=20.0)
    
    # get topo-maps
    topos = np.dot(ica.mixing_matrix_[:, :].T,
                   ica.pca_components_[:ica.n_components_])
    
    # compatibility section -- 3d interpolation to 4d sensorlayout

    predict_proba = classifier.predict_proba(topos)
    #art_inds = np.where(np.argmax(predict_proba,axis=1)<2)[0]
    art_inds = np.where(np.amax(predict_proba[:,0:2],axis=1)>thres)[0]

    # artifact annotation
    ica.exclude = art_inds
    
    return ica , predict_proba

# %% 

basename  = os.path.dirname(__file__) +"/" #'/home/nkampel/Playground/SVM_model/'  #change to project folder
#basename  = "./"
modelfile = basename + 'all_included_model.pckl'
# # load some .fif data

#Example 1: some nmag data
# systemtype='NMAG'
# fname =  basename + 'example_data/sample_audvis_raw.fif'
# raw = mne.io.read_raw_fif(fname, preload=True)

#Example 2: some 4d data
# systemtype='4d'
# fname =  basename + 'example_data/206719_LEDA01_130910_1102_2_c,rfDC_EC_bcc,nr,eeg-raw.fif'
# raw = mne.io.read_raw_fif(fname, preload=True)

#Example 3: some ctf data
systemtype='CTF'
fname = basename + 'example_data/anon01_MVNV3_01.ds'
raw = mne.io.read_raw_ctf(fname, preload=True)
 
random_time = np.random.randint(0,(raw.times[-1]-61))
raw.crop(random_time,random_time+60) # apply  to cropping  
# %%

#process the data


#raw.interpolate_bads()
raw.info['bads']= []
raw.filter(1,75) # filter


ica, predict_proba = get_ica_artifacts_compatible(raw,
                                                  modelfile,
                                                  systemtype= systemtype,
                                                  thres= 0.8)
#plot results
ica.plot_sources(raw)

# %%



















# %%




