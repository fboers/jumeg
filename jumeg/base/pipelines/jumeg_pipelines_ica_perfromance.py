#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 20.01.20
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

#from jumeg.decompose.ica_replace_mean_std import ICA, read_ica, apply_ica_replace_mean_std
#from jumeg.jumeg_preprocessing            import get_ics_cardiac, get_ics_ocular
#from jumeg.jumeg_plot                     import plot_performance_artifact_rejection  # , plot_artefact_overview

from jumeg.base.jumeg_base            import jumeg_base as jb
from jumeg.base.jumeg_base_config     import JuMEG_CONFIG_YAML_BASE as jCFG
from jumeg.base                       import jumeg_logger

from jumeg.base.pipelines.jumeg_pipelines_plot import JuMEG_ICA_PERFORMANCE_PLOT

#from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER

logger = logging.getLogger("jumeg")

__version__= "2019.12.12.001"


class _BASE(object):
    __slots__=[]
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
         raw:
         ch_name:
         set_annotations:
         event_id:
         tmin:
         tmax:
         verbose:
         debug:
         
         
         parameter for mne.preprocessing  find_ecg_events, find_eog_events
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
           channels      = [self.ch_name]
           evt_id        = [self.event_id]
        else:
           channels      = self.ch_name
           evt_id        = self.event_id
           
        while len(channels):
            ch_name  = channels.pop()
            event_id = evt_id.pop()
            
            if ch_name not in self.raw.info['ch_names']:
               continue
               
            self.events[ch_name]= dict()
            self.events[ch_name]["index"] = self.raw.ch_names.index(ch_name)
            res = self._call(self.raw,event_id,ch_name=ch_name,verbose=self.verbose)
           
            if isinstance(res[1],(np.ndarray)):
               self.events[ch_name]["events"] = res
               self.events[ch_name]["pulse"]  = self.events[ch_name]["events"].shape[0]
            else:
               self.events[ch_name]["events"] = res[0]
               self.events[ch_name]["pulse"] = res[2]
        
        if self.set_annotations:
           return self.set_anotations()
        return None

    def set_anotations(self):
        """
        update raw.anotattions with artefact events e.g.: ECG,EOG
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
        orig_time   = self.raw.info.get("meas_date",self.raw.times[0])


        for k in self.events.keys():
            msg = ["---> update raw.annotations: {}".format(k)]
    
            onset  = self.events[k]['events'][:,0] / self.raw.info["sfreq"]
            #onset -= self.tmin
            duration = np.ones( onset.shape[0] ) / self.raw.info["sfreq"]  # one line in raw.plot
            #duration+= abs(-self.tmin) + self.tmax
    
            evt_annot = mne.Annotations(onset=onset.tolist(),
                                        duration=duration.tolist(),
                                        description=k, # [condition for x in range(evt["events"].shape[0])],
                                        orig_time=orig_time)
            if raw_annot:
               msg.append(" --> found mne.annotations in RAW:\n  -> {}".format(raw_annot))
             #--- clear old annotations
               kidx = np.where( raw_annot.description == k)[0] # get index
               if kidx.any():
                  msg.append("  -> delete existing annotation {} counts: {}".format(k, kidx.shape[0]) )
                  raw_annot.delete(kidx)
                  
               self.raw.set_annotations( raw_annot + evt_annot)
               raw_annot = self.raw.annotations
            else:
               self.raw.set_annotations(evt_annot)
               raw_annot = self.raw.annotations
               
        msg.append(" --> storing mne.annotations in RAW:\n  -> {}".format(self.raw.annotations))
        logger.info("\n".join(msg))
        
        return self.raw.annotations

    def GetInfo(self,debug=False):
        if debug:
           self.debug=True
           
        if not isinstance(self.events,(dict)):
           logger.warning( "!!! --> Artefact Events: not events found !!!" )
           return
        
        msg = ["  --> Artefact Events:"]
        for k in self.events.keys():
            msg.extend( [" --> {}".format(k),"  -> pulse: {}".format( self.events[k]["pulse"] ) ] )
            if self.debug:
               msg.append( "  -> events:\n{}".format( self.events[k]["events"] ) )
               msg.append( "-"*25)
        logger.info( "\n".join(msg) )
        

class JuMEG_ICA_PERFORMANCE(_BASE):  # JuMEG_PLOT_BASE):
    """
    find ecg,eog artifacts in raw
     ->use jumeg or mne

    make mne.anotations
    prefromance check
     init array of figs : overview, n chops for ECg,EOG performance
     for each chop :
         avg epochs  => ECG plot raw, raw_cleaned evoked ,ECG signal, performance
                     => EOG plot raw, raw_cleaned evoked ,EOG signal, performance
    """
  #  raw=raw,path=path,fname=raw_fname,config=CFG.GetDataDict("ica")
    __slots__ = ["raw","path","fname","config","n_figs","_EOG","_ECG","_PLOT","picks","use_jumeg","ecg","eog","verbose"]
    
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._init(**kwargs)
        self._ECG = ARTEFACT_EVENTS(raw=self.raw,ch_name="ECG",event_id=999,tmin=-0.4,tmax=0.4,_call = find_ecg_events)
        self._EOG = ARTEFACT_EVENTS(raw=self.raw,ch_name=['EOG ver','EOG hor'],event_id=[997,998],tmin=-0.4,tmax=0.4,
                                    _call = find_eog_events)
        
        self._PLOT = JuMEG_ICA_PERFORMANCE_PLOT(**kwargs)
        
    @property
    def ECG(self): return self._ECG
    @property
    def EOG(self): return self._EOG
    @property
    def Plot(self): return self._PLOT


def test1():
    #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger)
    
    raw = None
    stage = "$JUMEG_PATH_LOCAL_DATA/exp/MEG94T/mne"
    fcfg  = os.path.join(stage,"meg94t_config01.yaml")
    fpath = "206720/MEG94T0T2/130820_1335/1/"
    
    path = os.path.join(stage,fpath)
    raw_fname = "206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
    
    logger.info("JuMEG Pipeline ICA Performance ICA mne-version: {}".format(mne.__version__))
    
    f = os.path.join(path,raw_fname)
    raw,raw_fname = jb.get_raw_obj(f,raw=None)

    raw_path = os.path.dirname(raw_fname)
   #--- get picks from raw
    picks = jb.picks.meg_nobads(raw)
  
   #---
    CFG = jCFG()
    CFG.update(config=fcfg)
    config = CFG.GetDataDict("ica")
   #--
    ICAPerformance = JuMEG_ICA_PERFORMANCE(raw=raw,path=path,fname=raw_fname,)
   
   #--- find ECG
    ICAPerformance.ECG.find_events(raw=raw,**config.get("ecg"))
    ICAPerformance.ECG.GetInfo(debug=True)
   #--- find EOG
    ICAPerformance.EOG.find_events(raw=raw,**config.get("eog"))
    ICAPerformance.EOG.GetInfo(debug=True)
   
   #---
    raw.plot(block=True)

   #--- save raw
   #fout=f.replace("-raw.fif","test-raw.fif")
   #jb.update_and_save_raw(raw,f,f)
   
def test2():
    #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger)
    
    raw = None
    stage = "$JUMEG_PATH_LOCAL_DATA/exp/MEG94T/mne"
    fcfg  = os.path.join(stage,"meg94t_config01.yaml")
    fpath = "206720/MEG94T0T2/130820_1335/1/"
    path = os.path.join(stage,fpath)

    fraw   =  "206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg,nr,bcc,int,000516-000645-raw.fif"
    fraw_ar = "206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg,nr,bcc,int,000516-000645,ar-raw.fif"
    
    
    
    logger.info("JuMEG Pipeline ICA Performance ICA mne-version: {}".format(mne.__version__))
   #---
    f = os.path.join(path,fraw)
    raw,raw_fname = jb.get_raw_obj(f,raw=None)
    raw_path      = os.path.dirname(raw_fname)
    picks         = jb.picks.meg_nobads(raw)
   #---
    f = os.path.join(path,fraw_ar)
    raw_ar,raw_ar_fname = jb.get_raw_obj(f,raw=None)
    
   #--- read config
    CFG = jCFG()
    CFG.update(config=fcfg)
    config = CFG.GetDataDict("ica")
    
   #---get annotations
    ids = { "ECG":1 }
    (events_from_annot,event_dict) = mne.events_from_annotations(raw_ar,event_id=ids)
    logger.info("---> events: {}\n {}".format(event_dict,events_from_annot))
   #--- do avg epochs MIn-MAX range
   
   #--- plot raw & raw_ar meg MIN-MAX + ECG as ref

    # ICAPerformance = JuMEG_ICA_PERFORMANCE(raw=raw,path=path,fname=raw_fname,)
   
    
    
if __name__ == "__main__":
    # test1()
    test2()