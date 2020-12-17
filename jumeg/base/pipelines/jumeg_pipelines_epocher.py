#!/usr/bin/env python3
# -+-coding: utf-8 -+-

#--------------------------------------------
# Authors:
# Frank Boers      <f.boers@fz-juelich.de>
# Christian Kiefer <c.kiefer@fz-juelich.de>
#--------------------------------------------
# Date: 2020.04.23
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,argparse

#---
from jumeg.base                           import jumeg_logger
from jumeg.base.jumeg_base                import jumeg_base   as jb
from jumeg.base.jumeg_base_config         import JuMEG_CONFIG as jCFG

from jumeg.epocher.jumeg_epocher          import JuMEG_Epocher

logger = jumeg_logger.get_logger()

__version__= "2020.04.23.001"

#---
from jumeg.base                           import jumeg_logger
from jumeg.base.jumeg_base                import jumeg_base as jb
from jumeg.base.jumeg_base                import JUMEG_SLOTS
from jumeg.base.jumeg_base_config         import JuMEG_CONFIG as jCFG
#---
#from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance  import JuMEG_ICA_PERFORMANCE
#from jumeg.base.pipelines.jumeg_pipelines_ica_svm          import JuMEG_ICA_SVM
#from jumeg.base.pipelines.jumeg_pipelines_chopper          import JuMEG_PIPELINES_CHOPPER
#---
from jumeg.epocher.jumeg_epocher   import JuMEG_Epocher
#---
#from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER

logger = jumeg_logger.get_logger()

__version__= "2020.04.22.001"


class JuMEG_PIPELIENS_EPOCHER(JUMEG_SLOTS):
    __slots__=["stage","path","subject_id","experiment",
               "ep_param","evt_param",
               "_plot_dir","report_key","path","fname","config","fname",
               "do_events","do_epochs","do_filter","verbose","debug","show",
               "_raw","_JuMEG_EPOCHER","_CFG"]
     
    
        #self.report_key     = "ica"
        
        #self._CFG           = jCFG(**kwargs)
        #self._plot_dir      = None
        #self._ics_found_svm = None
        
    
    def __init__(self,**kwargs):
        self._init(**kwargs)
        self._JuMEG_EPOCHER = JuMEG_Epocher()
        
        self._CFG       = jCFG(**kwargs)
        self._plot_dir   = "report"
        self.report_key = "epocher"
     
    
    @property
    def CFG(self): return self._CFG
    @property
    def cfg(self): return self._CFG._data
  
    @property
    def plot_dir(self): return os.path.join(self.path,self.cfg.plot_dir)
  
    @property
    def JuMEG_Epocher(self): return self._JuMEG_EPOCHER     
   #--- 
    @property
    def raw(self): return self._raw
    @raw.setter
    def raw(self,v): 
        self._raw = v
     
    def _update_from_kwargs(self,**kwargs):
        super()._update_from_kwargs(**kwargs)
        
        if "raw" in kwargs:
           self.raw = kwargs.get("raw")
     
    def _update_report(self,data):
        """
        
        :param fimages:
        :return:
        """
      #--- update report config
        CFG = jCFG()
        report_config = os.path.join(self.plot_dir,os.path.basename(self.raw_fname).rsplit("_",1)[0] + "-report.yaml")
        d = None
        if not CFG.load_cfg(fname=report_config):
            d = { "epocher":data }
        else:
            CFG.config["epocher"] = data
        CFG.save_cfg(fname=report_config,data=d)

    
    def run(self,**kwargs):
        #  jEP.run(stage=stage,subject_id=subject_id,experiment=experiment,path=path,fname=fname,config=config)    

        self._update_from_kwargs(**kwargs)
        # self._CFG.update(**kwargs )
      
       
        
        raw, fname = self.JuMEG_Epocher.apply_events(self.fname,raw=self.raw, **self.evt_param)
     
        raw, fname = self.JuMEG_Epocher.apply_epochs(self.fname,raw=self.raw, **self.ep_param)
       
        '''
       #--- Epocher events
        if self.do_events:
           logger.info("---> EPOCHER Events\n"+
                        "  -> FIF File      : {}\n".format(fname)+
                        "  -> FIF Path      : {}\n".format(fpath)+
                        "  -> Template      : {}\n".format(template_name)+
                        "  -> Template path : {}\n".format(template_path)+
                        "  -> HDF path      : {}\n".format(hdf_path)+
                        "  -> Epocher path  : {}\n".format(epocher_path)
                        )


           evt_param = {"condition_list": condition_list,
                        "template_path": template_path,
                        "template_name": template_name,
                        "hdf_path"     : hdf_path,
                        "verbose"      : verbose,
                        "debug"        : debug
                        }
           try:
                raw, fname = self.JuMEG_Epocher.apply_events(fraw,raw=raw, **evt_param)
           except:
                logger.exception(" error in calling jumeg_epocher.apply_events")

    
   #--- EPOCHER epochs
        if self.do_epochs:
           ep_param = {
                    "condition_list": condition_list,
                    "template_path": template_path,
                    "template_name": template_name,
                    "hdf_path"     : hdf_path,
                    "verbose"      : verbose,
                    "debug"        : debug,
                    "event_extention": ".eve",
                    "save_raw" : True, # mne .annotations
                    "output_mode":{ "events":True,"epochs":True,"evoked":True,"annotations":True,"stage":epocher_path,"use_condition_in_path":True}
                   
                    # "weights"       :{"mode":"equal","method":"median","skip_first":null}
                    # "exclude_events":{"eog_events":{"tmin":-0.4,"tmax":0.6} } },
                }
              # ---
            
            #logger.info("---> EPOCHER Epochs\n   -> File  :{}\n   -> Epocher Template: {}".format(fname,template_name))
           try:
               raw, fname = jumeg_epocher.apply_epochs(fname=fraw, raw=raw, **ep_param)
               #logger.info(raw.annotations)
               #raw.plot(butterfly=True,show=True,block=True,show_options=True)
           except:
               logger.exception(" error in calling jumeg_epocher.apply_epochs")
         
        logger.info("---> DONE EPOCHER Epochs\n   -> File  :{}\n   -> Epocher Template: {}".format(fname,template_name))
     
         
            
       #  self._update_report(data)
        '''
  
def test():
    '''
    from jumeg.base.jumeg_base                                 import jumeg_base as jb
    from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance  import ICAPerformance
    from jumeg.base.pipelines.jumeg_base_pipelines_chopper import JuMEG_PIPELINES_CHOPPER,copy_crop_and_chop,concat_and_save
    
    '''
   #---
    from jumeg.base.jumeg_base_config         import JuMEG_CONFIG as jCFG
    
    verbose=True
    debug=False
    
    stage= "$JUMEG_TEST_DATA/mne"
    #p  = "201772/INTEXT01/190212_1334/2"
    #fn = "201772_INTEXT01_190212_1334_2_c,rfDC,meeg,nr,bcc,int,ar-raw.fif"

    p = "208574/INTEXT01/190521_1416/1"
    fn= "208574_INTEXT01_190521_1416_1_c,rfDC,meeg,nr,bcc,int,ar-raw.fif"
    #fn   = "201772_INTEXT01_190212_1334_2_c,rfDC,meeg,nr,bcc,int,fibp0.10-45.0,ar-raw.fif"
    path = os.path.join(stage,p)
    fin  = os.path.join(path,fn)

    raw,fname = jb.get_raw_obj(fname=fin)
 
    #--- ck for annotations in raw 
    try:
      annota = raw.annotations
    except:
      from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance import ICAPerformance
      IP = ICAPerformance()
     #--- find ECG
      IP.ECG.find_events(raw=raw)
      IP.ECG.GetInfo(debug=True)
     #--- find EOG
      IP.EOG.find_events(raw=raw)
      IP.EOG.GetInfo(debug=True)
    
   #--- read epocher config 
   
   #--- define template
    template_path      = "$JUMEG_PATH_TEMPLATE_EPOCHER"
    template_name      = "INTEXT_001"
    template_extention = "jumeg_epocher_template.yaml"
   
   #--- CFG 
    CFG  = jCFG()
    fcfg = os.path.join(template_path, template_name + "_" + template_extention )
    
    CFG.update(config=fcfg)
    condition_list=[]
    
    for k,itm in CFG.config.items():
        if itm.get("run"):
           condition_list.append(k)
    
    if not condition_list: return

    epocher_path = os.path.join(os.path.dirname(fname),"epocher")
    hdf_path     = epocher_path
    
    evt_param = {"condition_list": condition_list,
                 "template_path": template_path,
                 "template_name": template_name,
                 "use_yaml"     : True,
                 "hdf_path"     : hdf_path,
                 "verbose"      : verbose,
                 "debug"        : debug
                }               
    
    ep_param = {
                "condition_list" : condition_list,
                "template_path"  : template_path,
                "template_name"  : template_name,
                "hdf_path"       : hdf_path,
                "save_raw"       : True, 
                "verbose"        : verbose,
                "debug"          : debug,
                "event_extention": ".eve",
                "output_mode"    :{"events":True,"epochs":True,"evoked":True,
                                   "annotations":True,
                                   "stage": epocher_path,
                                   "use_condition_in_path":True
                                  }
              # "weights"       :{"mode":"equal","method":"median","skip_first":null}
              # "exclude_events":{"eog_events":{"tmin":-0.4,"tmax":0.6} } },
                }
     
    jEP = JuMEG_PIPELIENS_EPOCHER()
   
    jEP.run(raw=raw,fname=fname,ep_param=ep_param,evt_param=evt_param,verbose=True,debug=False,show=True)

    #raw.plot(block=True,show=True)
   
   #---ToDo
   # use mne plots
    '''
       https://mne.tools/dev/auto_tutorials/preprocessing/plot_70_fnirs_processing.html#extract-epochs
       
       https://mne.tools/dev/auto_examples/visualization/plot_roi_erpimage_by_rt.html#sphx-glr-auto-examples-visualization-plot-roi-erpimage-by-rt-py
       
        epochs['Control'].plot_image(combine='mean', vmin=-30, vmax=30,
                                 ts_args=dict(ylim=dict(hbo=[-15, 15],
                                                        hbr=[-15, 15])))
    
    '''
        
    
if __name__ == "__main__":
    
   logger = jumeg_logger.setup_script_logging(logger=logger)
   test() 
    
    

