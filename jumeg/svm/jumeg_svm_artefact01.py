#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 13:12:26 2020
@author: nkampel
"""

import os,sys,argparse

import numpy as np
import pickle,logging

import mne
from mne.preprocessing import find_ecg_events, find_eog_events

from jumeg.base.jumeg_base   import jumeg_base as jb
from jumeg.base              import jumeg_logger
from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance import JuMEG_ICA_PERFORMANCE


logger = logging.getLogger("jumeg")

__version__= "2020.03.02.001"


#---- find artefacts with mne

class _BASE(object):
    __slots__ = []
    
    def __init__(self,**kwargs):
        super().__init__()
    
    def _init(self,**kwargs):
        #--- init slots
        for k in self.__slots__:
            self.__setattr__(k,None)
        self._update_from_kwargs(**kwargs)
    
    def _update_from_kwargs(self,**kwargs):
        if not kwargs: return
        for k in kwargs:
            try:
                if k in self.__slots__:
                    self.__setattr__(k,kwargs.get(k))
            except:
                pass
    
    def update(self,**kwargs):
        self._update_from_kwargs(**kwargs)


class ARTEFACT_EVENTS(_BASE):
    """
     artefact event dict:
       ch_name:  str or list of str
       event_id: int or list of int
       tmin: float tmin is s
       tmax: float tmax in s

     Example:
     --------
      ecg:
        ch_name: "ECG"
        event_id: 999
        tmin: -0.4
        tmax: 0.4

      eog:
       ch_name: ['EOG ver','EOG hor']
       event_id: [997,998]
       tmin: -0.4
       tmax: 0.4


       import mne,logging
       from mne.preprocessing import find_ecg_events, find_eog_events

       logger = logging.getLogger("jumeg")

      #--- find ECG
       ECG = ARTEFACT_EVENTS(raw=raw,ch_name="ECG",event_id=999,tmin=-0.4,tmax=0.4,_call = find_ecg_events)
       ECG.find_events(raw=raw,**config.get("ecg"))
       EOG.GetInfo(debug=True)

      #--- find EOG
       EOG = ARTEFACT_EVENTS(raw=raw,ch_name=['EOG ver','EOG hor'],event_id=[997,998],tmin=-0.4,tmax=0.4,
                                    _call = find_eog_events)
       EOG.find_events(raw=raw,**config.get("eog"))
       EOG.GetInfo(debug=True)

    """
    __slots__ = ["raw","ch_name","set_annotations","event_id","events","tmin","tmax","verbose","debug","_call"]
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._init(**kwargs)
        #--- default for set annotations = True
        self.set_annotations = kwargs.get("set_annotations",True)
    
    def find_events(self,**kwargs):
        """
         find ecg and eog events,
         update events in raw.Annotations
        
         raw            : raw obj
         ch_name: e.g.  : ECG,EOG ver,EOG hor
         set_annotations: <True>
         event_id       : 999,998,997
         tmin           : -0.4
         tmax           : 0.4
         verbose        : False
         debug          : False


         parameter for mne.preprocessing call to <find_ecg_events> & <find_eog_events>
          event_id=999, ch_name=None, tstart=0.0,
          l_freq=5, h_freq=35, qrs_threshold='auto',
          filter_length='10s', return_ecg=False,
          reject_by_annotation=None, verbose=None


         events={ ch_name: { events: <onsets> or  <mne.events>, # [onsets,offsets,id]
                             pulse: <event counts>}
         :return:
         if set annotations
            raw.annotations


        """
        self.update(**kwargs)
        self.events = dict()
        
        if not isinstance(self.ch_name,(list)):
            channels = [self.ch_name]
            evt_id = [self.event_id]
        else:
            channels = self.ch_name
            evt_id = self.event_id
        
        while len(channels):
            ch_name = channels.pop()
            event_id = evt_id.pop()
            
            if ch_name not in self.raw.info['ch_names']:
                continue
            
            self.events[ch_name] = dict()
            self.events[ch_name]["index"] = self.raw.ch_names.index(ch_name)
            res = self._call(self.raw,event_id,ch_name=ch_name,verbose=self.verbose)
            
            if isinstance(res[1],(np.ndarray)):
                self.events[ch_name]["events"] = res
                self.events[ch_name]["pulse"] = self.events[ch_name]["events"].shape[0]
            else:
                self.events[ch_name]["events"] = res[0]
                self.events[ch_name]["pulse"] = res[2]
        
        if self.set_annotations:
            return self.set_anotations()
        return None
    
    def set_anotations(self,save=False):
        """
        update raw.anotattions with artefact events e.g.: ECG,EOG
        save: save raw with annotations Talse
        return annotations

        """
        
        raw_annot = None
        evt_annot = None
        try:
            raw_annot = self.raw.annotations
        except:
            pass
        
        #--- store event info into raw.anotations
        time_format = '%Y-%m-%d %H:%M:%S.%f'
        orig_time = self.raw.info.get("meas_date",self.raw.times[0])
        
        for k in self.events.keys():
            msg = ["---> update raw.annotations: {}".format(k)]
            
            onset = self.events[k]['events'][:,0] / self.raw.info["sfreq"]
            #onset -= self.tmin
            duration = np.ones(onset.shape[0]) / self.raw.info["sfreq"]  # one line in raw.plot
            #duration+= abs(-self.tmin) + self.tmax
            
            evt_annot = mne.Annotations(onset=onset.tolist(),
                                        duration=duration.tolist(),
                                        description=k,  # [condition for x in range(evt["events"].shape[0])],
                                        orig_time=orig_time)
            if raw_annot:
                msg.append(" --> found mne.annotations in RAW:\n  -> {}".format(raw_annot))
                #--- clear old annotations
                kidx = np.where(raw_annot.description == k)[0]  # get index
                if kidx.any():
                    msg.append("  -> delete existing annotation {} counts: {}".format(k,kidx.shape[0]))
                    raw_annot.delete(kidx)
                
                self.raw.set_annotations(raw_annot + evt_annot)
                raw_annot = self.raw.annotations
            else:
                self.raw.set_annotations(evt_annot)
                raw_annot = self.raw.annotations
        
        if save:
            f = jb.get_raw_filename(raw)
            fanato = f.replace("-raw.fif","-anato.csv")
            self.raw.annotations.save(fanato)
        
        msg.append(" --> storing mne.annotations in RAW obj:\n  -> {}".format(self.raw.annotations))
        logger.info("\n".join(msg))
        
        return self.raw.annotations
    
    def GetInfo(self,debug=False):
        if debug:
            self.debug = True
        
        if not isinstance(self.events,(dict)):
            logger.warning("!!! --> Artefact Events: not events found !!!")
            return
        
        msg = ["  --> Artefact Events:"]
        for k in self.events.keys():
            msg.extend([" --> {}".format(k),"  -> pulse: {}".format(self.events[k]["pulse"])])
            if self.debug:
                msg.append("  -> events:\n{}".format(self.events[k]["events"]))
                msg.append("-" * 25)
        logger.info("\n".join(msg))




#--- SVM

class JuMEG_SVM_ARTEFACT():
    def __init__(self,**kwargs):
        self._raw        = None
        self._fname      = None
        self._models     = None
        self._systemtype = "4d"
        self._isModelLoaded = False
        
        self.model_name  = "all_included_model.pckl"
        self.model_path  = os.path.dirname(__file__)
        self.systemtypes = ['4d','nmag','ctf']
       #---
        self.do_copy = True
       #---
        self.do_crop = False
        self.tmin    = 0.
        self.tmax    = None
       #---
        self.sfreq  = 250
        self.n_jobs = 2
        self.l_freq = 2.
        self.h_freq = 50
        self.threshold    = 0.3
        self.n_components = 40
        self.method ='fastica'
      
    def update_from_kwargs(self,**kwargs):
        
        if kwargs.get("raw",None):
            self.raw = kwargs.get("raw")
        elif kwargs.get("fname",None): # full filepath
            self.raw,self._fname = jb.get_raw_obj(kwargs.get("fname"),raw=None)

        self.do_crop = kwargs.get("do_crop",self.do_crop)
        self.do_copy = kwargs.get("do_copy",self.do_copy)
        self.tmin    = kwargs.get("tmin",   self.tmin)
        self.tmax    = kwargs.get("tmax",   self.tmax)
       #---
        self.sfreq        = kwargs.get("sfreq", self.sfreq)
        self.n_jobs       = kwargs.get("n_jobs",self.n_jobs)
        self.l_freq       = kwargs.get("l_freq",self.l_freq)
        self.h_freq       = kwargs.get("h_freq",self.h_freq)
        self.threshold    = kwargs.get("threshold",self.threshold)
        self.n_components = kwargs.get("n_components",self.n_components)
        self.method       = kwargs.get("method",self.method)

        
        
    @property
    def systentype(self): return self._systemtype
    @systentype.setter
    def systemtype(self,type):
        if type in self.systemtypes:
           self._systemtype=type
           
           
    @property
    def isModelLoaded(self): return self._isModelLoaded
    
    @property
    def modelfile(self):
        return os.path.join(self.model_path,self.model_name)
    
    @property
    def classifier(self):
        if not self._isModelLoaded:
           self.load_model()
        return self._models[self.systemtype]

    def load_model(self):
        """
        load the SVM model only once
        :return:
        """
        self._isModelLoaded = False
        self._models        = pickle.load(open(self.modelfile,"rb"))
        self._isModelLoaded = True

    def _crop_raw(self,**kwargs):
        if self.do_crop:
            raw_c = self.raw.copy().crop(tmin=self.tmin,tmax=self.tmax)
        elif self.do_copy:
            raw_c = self.raw.copy()
        else:
            raw_c = self.raw
    
        return raw_c
    
    def _get_ica_artifacts_compatible(self,**kwargs):
        
        """Artifact removal using the mne ICA-decomposition
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
        self.update_from_kwargs(**kwargs)

      #--- we are fitting the ica on filtered copy of the original
        raw_c = self._crop_raw()

        raw_c.resample(sfreq=self.sfreq,n_jobs=self.n_jobs)
        raw_c.interpolate_bads()  # to get the dimesions right

        raw_c.filter(l_freq=self.l_freq,h_freq=self.h_freq)
        picks = mne.pick_types(raw_c.info,meg='mag',ref_meg=False)
        ica   = mne.preprocessing.ICA(n_components=self.n_components,method=self.method)
        ica.fit(raw_c,picks=picks)  # ,start=0.0,stop=20.0)
    
        # get topo-maps
        topos = np.dot(ica.mixing_matrix_[:,:].T,
                       ica.pca_components_[:ica.n_components_])
    
        # compatibility section -- 3d interpolation to 4d sensorlayout
    
        predict_proba = self.classifier.predict_proba(topos)
        #art_inds = np.where(np.argmax(predict_proba,axis=1)<2)[0]
        art_inds = np.where(np.amax(predict_proba[:,0:2],axis=1) > self.threshold)[0]
    
        # artifact annotation
        ica.exclude = art_inds
    
        return ica,predict_proba
    
    def run(self,**kwargs):
       # raw.filter(1,75)  # filter
        ica, predict_proba = self._get_ica_artifacts_compatible(**kwargs)
       #--- plot results
       # ica.plot_sources(self.raw)
      
        return ica, predict_proba




def run(opt):
    jumeg_logger.setup_script_logging(logger=logger)
    logger.info("---> JuMEG SVM ICA mne-version: {}".format(mne.__version__))
  
    jIP = JuMEG_ICA_PERFORMANCE()

  #--- init raw
    raw = None
    if opt.stage:    
       path = opt.stage
    if opt.path:
       path = os.path.join(path,opt.path)
   #--- init SVM class & run : load raw obj & apply SVM for ICs
    jSVM = JuMEG_SVM_ARTEFACT()
    fname= os.path.join(path,opt.fraw) 
    ica, predict_proba = jSVM.run( fname= fname )
    raw = jSVM.raw
     
   #--- raw cleaned
    raw_clean = ica.apply(raw.copy() )
  
    #raw.plot(block=True)
  
   #--- prepare performance plot
   #--- find ECG
    jIP.ECG.find_events(raw=raw)
   #--- find EOG in raw
    annotations = jIP.EOG.find_events(raw=raw)
    raw.set_annotations(annotations)
   #---  
    fout = fname.rsplit("-",1)[0] + "-ar"
    jIP.plot(raw=raw,raw_clean=raw_clean,verbose=opt.verbose,plot_path=path,fout=fout)

    jIP.Plot.figure.show()
    
    logger.info("---> DONE JuMEG SVM ICA")




def get_args(argv):
    """
    get args using argparse.ArgumentParser ArgumentParser
    e.g: argparse  https://docs.python.org/3/library/argparse.html
            
    Results:
    --------
    parser.parse_args(), parser
        
    """    
    info_global = """
                  JuMEG SVM

                  ---> merge eeg data with meg fif file 
                  jumeg_svm -f <xyz.fif> -p <path to fif file.> -v -d
                  """
            
   #--- parser
    parser = argparse.ArgumentParser(info_global)
 
   # ---meg input files
    parser.add_argument("-f", "--fraw",help="fif file")
    parser.add_argument("-p", "--path",help="path to fif file", default=".")
    parser.add_argument("-s", "--stage",help="stage path to fif file", default=".")
    parser.add_argument("-v", "--verbose", action="store_true",help="verbose mode")
    parser.add_argument("-d", "--debug",   action="store_true",help="debug mode")
  
   #---- ck if flag is set in argv as True
    opt = parser.parse_args()
        
    for g in parser._action_groups:
        for obj in g._group_actions:
            if str( type(obj) ).endswith('_StoreTrueAction\'>'):
               if vars( opt ).get(obj.dest):
                  opt.__dict__[obj.dest] = False
                  for flg in argv:
                      if flg in obj.option_strings:
                         opt.__dict__[obj.dest] = True
                         break
  
    return opt, parser


if __name__ == "__main__":

     
   if (len(sys.argv) < 1):
      parser.print_help()
      sys.exit()
   
   opt, parser = get_args(sys.argv)

   if opt.debug:
      opt.stage   = "/data/MEG/meg_store2/exp/JUMEGTest/mne/"
      opt.fraw    = "206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
      opt.path    = "206720/MEG94T0T2/130820_1335/1"
      opt.verbose = True

   run(opt)
  
