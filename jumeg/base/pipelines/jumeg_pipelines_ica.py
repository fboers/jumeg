#!/usr/bin/env python3
# -+-coding: utf-8 -+-

#--------------------------------------------
# Authors:
# Frank Boers      <f.boers@fz-juelich.de>
# Christian Kiefer <c.kiefer@fz-juelich.de>
#--------------------------------------------
# Date: 12.112.19
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,os.path as op
#import contextlib,

import logging,time,datetime
import mne
import numpy as np
from distutils.dir_util import mkpath

from jumeg.decompose.ica_replace_mean_std import ICA, read_ica, apply_ica_replace_mean_std
from jumeg.jumeg_preprocessing            import get_ics_cardiac, get_ics_ocular
# from jumeg.jumeg_plot                     import plot_performance_artifact_rejection  # , plot_artefact_overview

from jumeg.base.jumeg_base         import jumeg_base as jb
from jumeg.base.jumeg_base_config  import JuMEG_CONFIG_YAML_BASE as jCFG
from jumeg.base                    import jumeg_logger
from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER

logger = logging.getLogger("jumeg")

__version__= "2019.12.12.001"

'''
class JuMEG_ICA_CONFIG(JuMEG_CONFIG_YAML_BASE):
    """
    CLS for ICA config file obj

    Example:
    --------
    self.CFG = JuMEG_ICA_CONFIG(**kwargs)
    self.CFG.update(**kwargs)
    """
    
    def __init__(self,**kwargs):
        super().__init__()
'''

def apply_ica_and_plot_performance(raw, ica, name_ecg=None, name_eog=None, raw_fname=None, clean_fname=None,
                                   picks=None,reject=None, replace_pre_whitener=True, save=False):
    """
    Applies ICA to the raw object and plots the performance of rejecting ECG and EOG artifacts.

    Parameters
    ----------
    raw : mne.io.Raw()
        Raw object ICA is applied to
    ica : ICA object
        ICA object being applied d to the raw object
    name_ecg : str
        Name of the ECG channel in the raw data
    name_eog : str
        Name of the (vertical) EOG channel in the raw data
    raw_fname : str | None
        Path for saving the raw object
    clean_fname : str | None
        Path for saving the ICA cleaned raw object
    picks : array-like of int | None
        Channels to be included for the calculation of pca_mean_ and _pre_whitener.
        This selection SHOULD BE THE SAME AS the one used in ica.fit().
    reject : dict | None
        Rejection parameters based on peak-to-peak amplitude. This parameter SHOULD BE
        THE SAME AS the one used in ica.fit().
        Valid keys are 'grad', 'mag', 'eeg', 'seeg', 'ecog', 'eog', 'ecg',
        'hbo', 'hbr'.
        If reject is None then no rejection is done. Example::

            reject = dict(grad=4000e-13, # T / m (gradiometers)
                          mag=4e-12, # T (magnetometers)
                          eeg=40e-6, # V (EEG channels)
                          eog=250e-6 # V (EOG channels)
                          )

        It only applies if `inst` is of type Raw.
    replace_pre_whitener : bool
        If True, pre_whitener is replaced when applying ICA to
        unfiltered data otherwise the original pre_whitener is used.
    save : bool
        Save the raw object and cleaned raw object

    Returns
    -------
    raw_clean : mne.io.Raw()
        Raw object after ICA cleaning
    """

    # apply_ica_replace_mean_std processes in place -> need copy to plot performance
    #raw_copy = raw.copy()
    ica = ica.copy()

    raw_clean = apply_ica_replace_mean_std(raw, ica, picks=picks, reject=reject,
                                           exclude=ica.exclude, n_pca_components=None,
                                           replace_pre_whitener=replace_pre_whitener)
    if save:
        if raw_fname is not None:
           raw.save(raw_fname, overwrite=True)
        raw_clean.save(clean_fname, overwrite=True)

    overview_fname = clean_fname.rsplit('-raw.fif')[0] + ',overview-plot'
   
   #--- ToDo MNE reports
    plot_performance_artifact_rejection(raw, ica, overview_fname,
                                        meg_clean=raw_clean,
                                        show=False, verbose=False,
                                        name_ecg=name_ecg,
                                        name_eog=name_eog)
    print('Saved ', overview_fname)

    #raw_copy.close()
    
    return raw_clean


def fit_ica(raw, picks, reject, ecg_ch, eog_hor, eog_ver,
            flow_ecg, fhigh_ecg, flow_eog, fhigh_eog, ecg_thresh,
            eog_thresh, use_jumeg=True, random_state=42):
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
    
    logger.info('---> START ICA FIT: init ICA object')
    ica = ICA(method='fastica', n_components=40, random_state=random_state,
              max_pca_components=None, max_iter=5000, verbose=False)
    
    logger.info(' --> ICA FIT: apply ICA.fit')
    ica.fit(raw, picks=picks, decim=None, reject=reject, verbose=True)

    #######################################################################
    # identify bad components
    #######################################################################

    if use_jumeg:
        logger.info(" --> JuMEG Computing scores and identifying components ...")
       #--- get ECG related components using JuMEG
        ic_ecg,sc_ecg = get_ics_cardiac(raw, ica, flow=flow_ecg, fhigh=fhigh_ecg,
                                        thresh=ecg_thresh, tmin=-0.5, tmax=0.5, name_ecg=ecg_ch,
                                        use_CTPS=True) #[0]
        ic_ecg = list(set(ic_ecg))
        ic_ecg.sort()
      
       #--- get EOG related components using JuMEG
        ic_eog = get_ics_ocular(raw, ica, flow=flow_eog, fhigh=fhigh_eog,
                                       thresh=eog_thresh, name_eog_hor=eog_hor, name_eog_ver=eog_ver,
                                       score_func='pearsonr')
        ic_eog = list(set(ic_eog))
        ic_eog.sort()

       #--- if necessary include components identified by correlation as well
        bads_list = list(set(list(ic_ecg) + list(ic_eog)))
        bads_list.sort()
        ica.exclude = bads_list
        msg = [" --> JuMEG identified ICA components",
               "  -> ECG components: {}".format(ic_ecg),
               "  ->         scores: {}".format(sc_ecg[ic_ecg]),
               "  -> EOG components: {}".format(ic_eog)
              ]
        logger.debug("\n".join(msg))
    else:
        logger.info(" --> MNE Computing scores and identifying components ...")
        ecg_scores = ica.score_sources(raw, target=ecg_ch, score_func='pearsonr',
                                       l_freq=flow_ecg, h_freq=fhigh_ecg, verbose=False)
        # horizontal channel
        eog1_scores = ica.score_sources(raw, target=eog_hor, score_func='pearsonr',
                                        l_freq=flow_eog, h_freq=fhigh_eog, verbose=False)
        # vertical channel
        eog2_scores = ica.score_sources(raw, target=eog_ver, score_func='pearsonr',
                                        l_freq=flow_eog, h_freq=fhigh_eog, verbose=False)

        # print the top ecg, eog correlation scores
        ecg_inds = np.where(np.abs(ecg_scores) > ecg_thresh)[0]
        eog1_inds = np.where(np.abs(eog1_scores) > eog_thresh)[0]
        eog2_inds = np.where(np.abs(eog2_scores) > eog_thresh)[0]

        highly_corr = list(set(np.concatenate((ecg_inds, eog1_inds, eog2_inds))))
        highly_corr.sort()

        highly_corr_ecg = list(set(ecg_inds))
        highly_corr_eog1 = list(set(eog1_inds))
        highly_corr_eog2 = list(set(eog2_inds))

        highly_corr_ecg.sort()
        highly_corr_eog1.sort()
        highly_corr_eog2.sort()

        # if necessary include components identified by correlation as well
        ica.exclude = highly_corr
        msg = ["  -> MNE Highly correlated artifact components",
               "  -> ECG  : {} ".format(highly_corr_ecg),
               "  -> EOG 1: {} ".format(highly_corr_eog1),
               "  -> EOG 2: {} ".format(highly_corr_eog2)
               ]
               
        logger.debug("\n".join(msg))
   
    logger.info(" --> done ICA FIT\n  -> excluded ICs: {}\n".format(ica.exclude))
    return ica
 


def plot_performance_artifact_rejection(meg_raw, ica, fnout_fig,
                                        meg_clean=None, show=False,
                                        proj=False, verbose=False,
                                        name_ecg='ECG 001', name_eog='EOG 002'):
    '''
    Creates a performance image of the data before
    and after the cleaning process.
    '''

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


    
class JuMEG_PIPELINES_ICA(object):
    def __init__(self,**kwargs):
        super().__init__()
        self._CFG      = jCFG(**kwargs)
        self.PreFilter = JuMEG_MNE_FILTER()
        self._clear()
   
    @property
    def stage(self): return self._stage
    @stage.setter
    def stage(self,v):
        self._stage=v
    
    @property
    def path(self): return self._raw_path
    @path.setter
    def path(self,v):
        if v:
           self._raw_path = jb.isPath(v)
       
    @property
    def path_ica(self): return os.path.join(self.path,"ica")
    @property
    def path_ica_chops(self): return os.path.join(self.path_ica,"chops")
    
    @property
    def raw(self): return self._raw

    @property
    def raw_fname(self): return self._raw_fname

    @raw_fname.setter
    def raw_fname(self,v):
        self._raw_fname = jb.isFile(v,path=self.path)

    @property
    def picks(self): return self._picks
    
    @property
    def CFG(self): return self._CFG
    @property
    def cfg(self): return self._CFG._data

    def _clear(self):
        self._start_time = time.time()
        self._stage     = None
        self._path      = None
        self._path_ica  = None

        self._raw       = None
        self._raw_path  = None
        self._raw_fname = None
        self._raw_isfiltered = False
        
        self._ica_obj    = None
        self._picks      = None
        self._chop_times = None
        self._filter_prefix = ""
        self._filter_fname  = ""
        
    def _update_from_kwargs(self,**kwargs):
        self._raw      = kwargs.get("raw",self._raw)
        self.path      = kwargs.get("path",self._path)
        self._stage    = kwargs.get("stage",self.stage)
        self.raw_fname = kwargs.get("raw_fname",self._raw_fname)

    def trunc_nd(self,n,d):
        """
        https://stackoverflow.com/questions/8595973/truncate-to-three-decimals-in-python/8595991
        """
        n = str(n)
        return (n if not n.find('.') + 1 else n[:n.find('.') + d + 1])

    #--- calc chop times
    def _calc_chop_times(self):
        logger.debug("  -> Start calc Chop Times: length: {} raw time: {}".format(self.cfg.chops.length,self.raw.times[-1]))
        self._chop_times = None
        
        if self.raw.times[-1] <= self.cfg.chops.length:
           cps      = np.zeros([1,2],dtype=np.float32)
           cps[0,0] = 0.0
           logger.warning("---> <Raw Times> : {} smaler than <Chop Times> : {}\n\n".format(self.raw.times[-1],self._chop_times))
        else:
           n_chops,t_rest = np.divmod(self.raw.times[-1],self.cfg.chops.length)
           n_chops = int(n_chops)
           dtime   = self.cfg.chops.length + t_rest // n_chops # add rest to length
        
           cps          = np.zeros([n_chops,2],dtype=np.float32)
           cps[:,0]    += np.arange(n_chops) * dtime
           cps[0:-1,1] += cps[1:,0]
        #cps[-1,1]    = '%.3f'%( self.raw.times[-1] ) # ???? error in mne crop line 438
        # fb 01.11.2019
        
        cps[-1,1] = None #self.trunc_nd(self.raw.times[-1], 3)  # ???? error in mne crop line 438 mne error tend == or less tmax
        self._chop_times = cps
        
        logger.debug("  -> Chop Times:\n{}".format(self._chop_times))
        return self._chop_times

   #--- calc chop times from events
    def _calc_chop_times_from_events(self):
        
        logger.info("  -> Chop Times:\n{}".format(self._chop_times))
        return self._chop_times

    def _copy_crop_and_chop(self,raw,chop):
        """
        copy raw
        crop
        :param raw:
        :param chop:
        :return:
        """
        if self._chop_times.shape[0] > 1:
            return raw.copy().crop(tmin=chop[0],tmax=chop[1])
        return raw

    def _initRawObj(self):
        """
        load or get RAW obj
        init & mkdir path tree  <stage>/../ica/chops
        init picks from RAW
        """
        self._raw,self._raw_fname = jb.get_raw_obj(self.raw_fname,raw=self.raw)
    
        self._raw_path = os.path.dirname(self._raw_fname)
        if self.stage:
            self._raw_path = os.join(self.stage,self._raw_path)
        #---
        mkpath(self.path_ica_chops,mode=0o770)
    
        #--- get picks from raw
        self._picks = jb.picks.meg_nobads(self._raw)

    def _get_chop_name(self,raw,chop=None,extention="-ica.fif",postfix=None,fullpath=False):
        """
        raw
        chop     = None
        extention= "-ica.fif" [-raw.fif]
        postfix  = None      [ar]
        fullpath = True
                   if True: includes path in filename
        Return:
        -------
        fname chop,fname orig
        """
        fname = jb.get_raw_filename(raw)
        fname,fextention = op.basename(fname).rsplit('-',1)
        if fullpath:
           if fname.startswith(self.path_ica_chops):
              fchop = fname
           else:
              fchop = op.join(self.path_ica_chops,fname)
        else:
           fchop = os.path.basename(fname)
           
        if postfix:
           fchop +=","+postfix
        try:
           if len(chop):
              if np.isnan(chop[1]):
                 fchop += ',{:06d}-{:06d}'.format(int(chop[0]),int(self.raw.times[-1]))
              else:
                 fchop += ',{:06d}-{:06d}'.format(int(chop[0]),int(chop[1]))
        except:
            pass
        if extention:
           fchop+=extention
    
        return fchop,fname
   
    def _apply_fit(self,raw_chop=None,chop=None,idx=None):
        """
        raw_chop = None
        chop     = None
        
        ToDo
        if not overwrite
          if ICA file exist: load ICA
          else calc ICA
        
        :return:
        ICA obj, ica-filename
        """
        self._ica_obj = None
        fname_ica,fname = self._get_chop_name(raw_chop,chop=None)
      
        logger.info("---> start ICA FIT chop: {} / {}\n".format(idx + 1,self._chop_times.shape[0]) +
                    " --> chop id      : {}\n".format(chop) +
                    "  -> ica fname    : {}\n".format(fname_ica) +
                    "  -> ica chop path: {}\n".format(self.path_ica_chops) +
                    "  -> raw filename : {}\n".format(fname))
     
       #--- ck for ovewrite & ICA exist
        load_from_disk = False
        if not self.cfg.fit.overwrite:
           load_from_disk = jb.isFile(fname_ica,path=self.path_ica_chops)
        
        if load_from_disk:
           self._ica_obj,fname_ica = jb.get_raw_obj(fname_ica,path=self.path_ica_chops)
           logger.info("---> DONE LOADING ICA chop form disk: {}\n  -> ica filename: {}".
                       format(chop,fname_ica))
        else:

        #   with jumeg_logger.StreamLoggerSTD(label="ICA FIT"): #log print()
           self._ica_obj = fit_ica(raw=raw_chop,picks=self.picks,reject=self.CFG.GetDataDict(key="reject"),
                                   ecg_ch=self.cfg.ecg.channel,ecg_thresh=self.cfg.ecg.thresh,
                                   flow_ecg=self.cfg.ecg.flow,fhigh_ecg=self.cfg.ecg.fhigh,
                                  #---
                                   eog_hor = self.cfg.eog.hor_ch,
                                   eog_ver = self.cfg.eog.ver_ch,
                                   flow_eog=self.cfg.eog.flow,fhigh_eog=self.cfg.eog.fhigh,
                                   eog_thresh=self.cfg.eog.thresh,
                                  #---
                                   use_jumeg=self.cfg.ecg.use_jumeg,
                                   random_state=self.cfg.random_state)
          #--- save ica object
           if self.cfg.fit.save:
              logger.info("---> saving ICA chop: {}\n".format(idx + 1,self._chop_times.shape[0]) +
                          "  -> ica filename   : {}".format(fname_ica))
              self._ica_obj.save(os.path.join(self.path_ica_chops,fname_ica))
              
        logger.info("---> done ICA FIT for chop: {}\n".format(chop)+
                    "  -> raw chop filename    : {}\n".format(fname_ica)+
                    "  -> save ica fit         : {}".format(self.cfg.fit.save)
                   )
    
        return self._ica_obj,fname_ica

    def _apply_transform(self,raw_chop,ICA,fname_raw= None,fname_clean=None,save=None):
        """
         call  apply_ica_and_plot_performance()
        :param raw_chop:
        :param ICA:
        :return:
        """
        logger.info("---> Start ICA Transform")
     
        return apply_ica_and_plot_performance(raw_chop,ICA,
                                              name_ecg    = self.cfg.ecg.channel,
                                              name_eog    = self.cfg.eog.ver_ch,
                                              raw_fname   = fname_raw,
                                              clean_fname = fname_clean,
                                             #---
                                              picks  = self.picks,
                                              reject = self.CFG.GetDataDict(key="reject"),
                                              save   = save,
                                              replace_pre_whitener = True
                                            )
    
    def concat_and_save(self,raws,fname=None,save=False):
        """
        concat a list of raw obj
        call to mne.concatenate_raw
        
        :param raws:
        :param save: save concat raw
        :return:
         concat raw obj
        """
        if raws:
           raw_concat = mne.concatenate_raws(raws)
           while raws:
               raws.pop().close()
           if fname:
               jb.set_raw_filename(raw_concat,fname)
           if save:
              jb.apply_save_mne_data(raw_concat,fname=fname)
              
        return raw_concat

    def run(self,**kwargs):
        """
        
        :param kwargs:
        :return:
        raw_unfiltered_clean,raw_filtered_clean
        
        """
        self._clear()
        self._update_from_kwargs(**kwargs)
      #--- load config
        self._CFG.update(**kwargs)
 
      #--- init or load raw
        self._initRawObj()
  
      #--- chop times
        if self.cfg.chops.epocher.use:
            """ToDo use epocher information chop onset,offset"""
            pass
        else:
            self._calc_chop_times()
        
        if not isinstance(self._chop_times,(np.ndarray)):
           logger.exception("---> No <chop times> defined for ICA\n" +
                             "  -> raw filename : {}\n".format(self._raw_fname))
           return None
       
       #--- chops as string
        s = ""
        for cp in self._chop_times:
            s+="{}-{}  ".format(cp[0],cp[1])
            
        msg = [
            "---> Apply ICA => FIT & Transform",
            "  -> filename      : {}".format(self._raw_fname),
            "  -> ica chop path : {}".format(self.path_ica_chops),
            "  -> chops         : {}".format(s),
            "-" * 40
            ]

        if self.cfg.pre_filter.run:
          #--- do filter
           self.PreFilter.apply(
                   flow      = self.cfg.pre_filter.flow,
                   fhigh     = self.cfg.pre_filter.fhigh,
                   save      = self.cfg.pre_filter.save,
                   raw       = self.raw.copy(),
                   picks     = self.picks,
                  )
           msg = self.PreFilter.GetInfo(msg=msg)
        else:
           self.PreFilter.clear()
           
        logger.info("\n".join(msg) )
       
       #--- reset output
        raw_filtered_clean = None
        raw_filtered_chops_clean_list = []
       #---
        raw_unfiltered_clean = None
        raw_unfiltered_chops_clean_list = []
    
       #--- loop for chpos
        for idx in range(self._chop_times.shape[0]):
            chop = self._chop_times[idx]
          
            logger.info("---> Start ICA FIT & Transform chop: {} / {}\n".format(idx + 1,self._chop_times.shape[0]))
    
            if self.PreFilter.isFiltered:
               raw_chop = self._copy_crop_and_chop(self.PreFilter.raw,chop)
            else:
               raw_chop = self._copy_crop_and_chop(self.raw,chop)
 
           #---  ICA FIT filtered or unfilterd obj
            fname_chop,fname_raw = self._get_chop_name(raw_chop,chop=chop,extention="-raw.fif")
            jb.set_raw_filename(raw_chop,fname_chop)
            ICA,fname_ica = self._apply_fit(raw_chop=raw_chop,chop=chop,idx=idx)
       
           #--- ICA Transform
            if self.cfg.transform.run:
              #--- filtered
               if self.cfg.transform.filtered.run:
                  if self.PreFilter.isFiltered:
                  #--- filtered
                     fname_chop,_  = self._get_chop_name(raw_chop,extention="-raw.fif")
                     fname_filtered_clean,_ = self._get_chop_name(raw_chop,extention="-raw.fif",postfix="ar")
                     raw_filtered_chops_clean_list.append( self._apply_transform(raw_chop,ICA,
                                                                fname_raw   = fname_chop,
                                                                fname_clean = fname_filtered_clean,
                                                                save        = self.cfg.transform.filtered.save_chops))
                                         
             #--- unliterd
               if self.cfg.transform.unfiltered.run:
                  raw_chop      = self._copy_crop_and_chop(self.raw,chop)
                  fname_chop,_  = self._get_chop_name(raw_chop,extention="-raw.fif")
                  fname_unfiltered_clean,_ = self._get_chop_name(raw_chop,extention="-raw.fif",postfix="ar")
                  raw_unfiltered_chops_clean_list.append( self._apply_transform(raw_chop,ICA,
                                                               fname_raw   = fname_chop,
                                                               fname_clean = fname_unfiltered_clean,
                                                               save        = self.cfg.transform.unfiltered.save_chops) )
                  
            logger.info(" --> done ICA FIT & transform chop: {} / {}\n".format(idx + 1,self._chop_times.shape[0]))
            
       #--- concat filtered raws
        if raw_filtered_chops_clean_list:
           raw_filtered_clean = self.concat_and_save(raw_filtered_chops_clean_list,
                                                       fname = self.PreFilter.fname.replace("-raw.fif",",ar-raw.fif"),
                                                       save  = self.cfg.transform.filtered.save)
       #--- concat unfiltered raws
        if raw_unfiltered_chops_clean_list:
           raw_unfiltered_clean = self.concat_and_save(raw_unfiltered_chops_clean_list,
                                                         fname = self._raw_fname.replace("-raw.fif",",ar-raw.fif"),
                                                         save  = self.cfg.transform.unfiltered.save)
        logger.info("---> DONE ICA FIT & Transpose\n"+
                    "  -> filename : {}\n".format( jb.get_raw_filename(raw_unfiltered_clean) )+
                    "  -> time to process :{}".format( datetime.timedelta(seconds= time.time() - self._start_time ) ))
      
        return raw_unfiltered_clean,raw_filtered_clean
       

if __name__ == "__main__":
  
  #--- init/update logger
   jumeg_logger.setup_script_logging(logger=logger)
 
   stage = "${JUMEG_TEST_DATA}/mne"
   fcfg  = "intext_config01.yaml"
   
   raw       = None
   fpath     = "211855/INTEXT01/190329_1004/6"
   path      = os.path.join(stage,fpath)
   # raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc-raw.fif"
   raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc,int-raw.fif"

   logger.info("JuMEG Apply ICA mne-version: {}".format(mne.__version__))
 #--
   jICA = JuMEG_PIPELINES_ICA()
   jICA.run( path=path,raw_fname=raw_fname,config=fcfg,key="ica")


