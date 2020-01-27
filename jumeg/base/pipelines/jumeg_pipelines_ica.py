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

import numpy as np
from distutils.dir_util import mkpath

import matplotlib.pyplot as pl

import mne
from mne.preprocessing import find_ecg_events, find_eog_events

from jumeg.decompose.ica_replace_mean_std import ICA, read_ica, apply_ica_replace_mean_std
from jumeg.jumeg_preprocessing            import get_ics_cardiac, get_ics_ocular
# from jumeg.jumeg_plot                     import plot_performance_artifact_rejection  # , plot_artefact_overview

from jumeg.base                    import jumeg_logger
from jumeg.base.jumeg_base         import jumeg_base as jb
from jumeg.base.jumeg_base_config  import JuMEG_CONFIG_YAML_BASE as jCFG
from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance  import JuMEG_ICA_PERFORMANCE

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


#######################################################
#
#  calculate the frequency-correlation value
#
#######################################################
def calc_frequency_correlation(evoked_raw, evoked_clean):

    """
    Function to estimate the frequency-correlation value
    as introduced by Krishnaveni et al. (2006),
    Journal of Neural Engineering.
    """

    # transform signal to frequency range
    fft_raw = np.fft.fft(evoked_raw.data)
    fft_cleaned = np.fft.fft(evoked_clean.data)

    # get numerator
    numerator = np.sum(np.abs(np.real(fft_raw) * np.real(fft_cleaned)) +
                       np.abs(np.imag(fft_raw) * np.imag(fft_cleaned)))

    # get denominator
    denominator = np.sqrt(np.sum(np.abs(fft_raw) ** 2) *
                          np.sum(np.abs(fft_cleaned) ** 2))

    return np.round(numerator / denominator * 100.)

#######################################################
#
#  calculate the performance of artifact rejection
#
#######################################################
def calc_performance(evoked_raw, evoked_clean):
    ''' Gives a measure of the performance of the artifact reduction.
        Percentage value returned as output.
    '''
    from jumeg import jumeg_math as jmath

    diff = evoked_raw.data - evoked_clean.data
    rms_diff = jmath.calc_rms(diff, average=1)
    rms_meg = jmath.calc_rms(evoked_raw.data, average=1)
    arp = (rms_diff / rms_meg) * 100.0
    return np.round(arp)


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
        bads_list = []
        bads_list.extend( ic_ecg )
        bads_list.extend( ic_eog )
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


class JuMEG_PIPELINES_ICA(object):
    def __init__(self,**kwargs):
        super().__init__()
        self._CFG           = jCFG(**kwargs)
        self.PreFilter      = JuMEG_MNE_FILTER()
        self.ICAPerformance = JuMEG_ICA_PERFORMANCE()
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
        call to jumeg fit_ica
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
                                   ecg_ch=self.cfg.ecg.ch_name,ecg_thresh=self.cfg.ecg.thresh,
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

   #--- apply ica transform
    def apply_ica_artefact_rejection(self,raw,ICA,fname_raw= None,fname_clean=None,replace_pre_whitener=True,save_chop=False):
        """
        Applies ICA to the raw object.

        Parameters
        ----------
            raw : mne.io.Raw()  (raw chop)
                  Raw object ICA is applied to
            ica : ICA object
                  ICA object being applied d to the raw object
            fname_raw : str | None
                  Path for saving the raw object
            fname_clean : str | None
                  Path for saving the ICA cleaned raw object
            picks : array-like of int | None
                  Channels to be included for the calculation of pca_mean_ and _pre_whitener.
                  This selection SHOULD BE THE SAME AS the one used in ica.fit().
            replace_pre_whitener : bool
                  If True, pre_whitener is replaced when applying ICA to
                  unfiltered data otherwise the original pre_whitener is used.
            save_chop: bool
                  Save the raw object and cleaned raw object

        Returns
        -------
            raw_clean : mne.io.Raw()
                       Raw object after ICA cleaning
        """
        logger.info("---> Start ICA Transform")
     
        ica = ICA.copy()
        # raw = raw_chop.copy()
        
        raw_clean = apply_ica_replace_mean_std(raw,ica,picks=self.picks,
                                               reject=self.CFG.GetDataDict(key="reject"),
                                               exclude=ica.exclude,n_pca_components=None,
                                               replace_pre_whitener=replace_pre_whitener)
        if save_chop:
            if fname_raw is not None:
                raw.save(fname_raw,overwrite=True)
            raw_clean.save(fname_clean,overwrite=True)
   
        return raw_clean

    def concat_and_save(self,raws,fname=None,save=False,annotations=None):
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
              if not fname.startswith(self.path):
                 fname = os.path.join(self.path,fname)
              jb.apply_save_mne_data(raw_concat,fname=fname)
           
           if annotations:
              raw_concat.set_annotations(annotations)
              
        return raw_concat

#==== MAIN function
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

       #--- init ICAPerformance get ecg & eog events
       #--- find ECG in raw
        self.ICAPerformance.ECG.find_events(raw=self.raw,**self.CFG.GetDataDict("ecg"))
        # self.ICAPerformance.ECG.GetInfo(debug=self.debug)
        
       #--- find EOG in raw
        annotations = self.ICAPerformance.EOG.find_events(raw=self.raw,**self.CFG.GetDataDict("eog"))
        self.raw.set_annotations(annotations)
        
        # self.ICAPerformance.EOG.GetInfo(debug=self.debug)

       #--- logger INFO
        s = ""
        for cp in self._chop_times:   # chops as string
            s+="{}-{}  ".format(cp[0],cp[1])
            
        msg = [
            "---> Apply ICA => FIT & Transform",
            "  -> filename      : {}".format(self._raw_fname),
            "  -> ica chop path : {}".format(self.path_ica_chops),
            "  -> chops         : {}".format(s),
            "-" * 40
            ]
       #--- apply pre-filter
        if self.cfg.pre_filter.run:
           self.PreFilter.apply(
                   flow      = self.cfg.pre_filter.flow,
                   fhigh     = self.cfg.pre_filter.fhigh,
                   save      = self.cfg.pre_filter.save,
                   raw       = self.raw.copy(),
                   picks     = self.picks,
                   annotations = annotations
                  )
           
           msg = self.PreFilter.GetInfo(msg=msg)
    
        else:
           self.PreFilter.clear()
           
        logger.info("\n".join(msg) )
     
       #--- init performance plots for raw vs clean  & chops
        self.ICAPerformance.Plot.init(n_figs=self._chop_times.shape[0] + 1)

       
       TODO check annotations  set for raw ar cleaned  and_saved
       
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
           
           #--- plot performance chop raw
            
            ICA,fname_ica = self._apply_fit(raw_chop=raw_chop,chop=chop,idx=idx)
       
           #--- ICA Transform
            if self.cfg.transform.run:
              #--- filtered
               if self.cfg.transform.filtered.run:
                  if self.PreFilter.isFiltered:
                  #--- filtered
                     fname_chop,_  = self._get_chop_name(raw_chop,extention="-raw.fif")
                     fname_filtered_clean,_ = self._get_chop_name(raw_chop,extention="-raw.fif",postfix="ar")
                     raw_filtered_chops_clean_list.append( self.apply_ica_artefact_rejection(raw_chop,ICA,
                                                                fname_raw   = fname_chop,
                                                                fname_clean = fname_filtered_clean,
                                                                save_chop  = self.cfg.transform.filtered.save_chop))
                                         
             #--- unliterd
               if self.cfg.transform.unfiltered.run:
                  raw_chop      = self._copy_crop_and_chop(self.raw,chop)
                  fname_chop,_  = self._get_chop_name(raw_chop,extention="-raw.fif")
                  fname_unfiltered_clean,_ = self._get_chop_name(raw_chop,extention="-raw.fif",postfix="ar")
                  raw_unfiltered_chops_clean_list.append( self.apply_ica_artefact_rejection(raw_chop,ICA,
                                                               fname_raw   = fname_chop,
                                                               fname_clean = fname_unfiltered_clean,
                                                               save_chop  = self.cfg.transform.unfiltered.save_chop) )
                  
            logger.info(" --> done ICA FIT & transform chop: {} / {}\n".format(idx + 1,self._chop_times.shape[0]))
            
       #--- concat filtered raws
        if raw_filtered_chops_clean_list:
           raw_filtered_clean = self.concat_and_save(raw_filtered_chops_clean_list,
                                                       fname       = self.PreFilter.fname.replace("-raw.fif",",ar-raw.fif"),
                                                       annotations = self.raw.annotations,
                                                       save        = self.cfg.transform.filtered.save)
       #--- concat unfiltered raws
        if raw_unfiltered_chops_clean_list:
           raw_unfiltered_clean = self.concat_and_save(raw_unfiltered_chops_clean_list,
                                                         fname       = self._raw_fname.replace("-raw.fif",",ar-raw.fif"),
                                                         annotations = self.raw.annotations,
                                                         save        = self.cfg.transform.unfiltered.save
                                                       )
        logger.info("---> DONE ICA FIT & Transpose\n"+
                    "  -> filename : {}\n".format( jb.get_raw_filename(raw_unfiltered_clean) )+
                    "  -> time to process :{}".format( datetime.timedelta(seconds= time.time() - self._start_time ) ))
      
        return raw_unfiltered_clean,raw_filtered_clean
       

def test1():
   #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger)
    
    stage = "$JUMEG_PATH_LOCAL_DATA/exp/MEG94T/mne"
    fcfg  = os.path.join(stage,"meg94t_config01.yaml")
    fpath = "206720/MEG94T0T2/130820_1335/1/"
    
    path = os.path.join(stage,fpath)
    raw_fname = "206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
   
    #stage = "${JUMEG_TEST_DATA}/mne"
    #fcfg = "intext_config01.yaml"
    
    raw = None
    #fpath = "211855/INTEXT01/190329_1004/6"
    #path = os.path.join(stage,fpath)
    # raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc-raw.fif"
    #raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc,int-raw.fif"
    
    logger.info("JuMEG Apply ICA mne-version: {}".format(mne.__version__))
    #--
    jICA = JuMEG_PIPELINES_ICA()
    jICA.run(path=path,raw_fname=raw_fname,config=fcfg,key="ica")



if __name__ == "__main__":
  test1()
  
