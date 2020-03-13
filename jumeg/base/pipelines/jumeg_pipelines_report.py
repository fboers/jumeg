#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 16.12.19
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------


import os,logging
from distutils.dir_util import mkpath

#import pandas as pd
#from PIL import Image

import warnings
import mne
from mne.report import Report


from jumeg.base.jumeg_base         import JUMEG_SLOTS
from jumeg.base.jumeg_base         import jumeg_base as jb

from jumeg.base.jumeg_base_config  import JuMEG_CONFIG as jCFG
from jumeg.base                    import jumeg_logger


__version__= "2019.12.16.001"

logger = logging.getLogger("jumeg")

class MNE_REPORT(JUMEG_SLOTS):
    """
    saving
     noise_reducer fig
     ica figs in HDF
     epocher figs

    and show in MNE Reports
    """
    __slots__ = { "postfix","extention","info_name",
                  "title","open_browser","write_hdf5","raw_psd","image_format","overwrite","verbose",
                  "_fname","_isOpen","_path","_fhdf","_MNE_REPORT"}
    
    def __init__(self,**kwargs):
        super().__init__()
        self._init()
        
        self._path        = "."
       #---
        self.image_format = "png"
        self.postfix      = "report"
        self.extention    = ".html"
        self.raw_psd      = False
        
        self._update_from_kwargs(**kwargs)
        
    @property
    def path(self):
        return self._path

    @path.setter
    def path(self,v):
        if v:
           self._path = jb.expandvars(v)
           mkpath(self._path,mode=0o770)
        else:
            self._path=v
    
    @property
    def fname(self):
        if not self._fname.endswith(self.postfix + self.extention):
           return self._fname + "-" + self.postfix + self.extention
        return self._fname
    
    @fname.setter
    def fname(self,v):
        self._fname=v
        #if not self._fname.endswith( self.postfix+self.extention )
        #   self._fname += self.postfix+self.extention
        
    @property
    def fullname(self):
        return os.path.join(self.path,self.fname)
    @property
    def image_extention(self): return "."+self.image_format
    
    @property
    def isOpen(self): return self._isOpen

    @property
    def MNEreport(self): return self._MNE_REPORT
    
    @property
    def fhdf(self): return self._fhdf
    @fhdf.setter
    def fhdf(self,v):
        self._fhdf = jb.expandvars(v)
        mkpath(os.path.dirname(self._fhdf),mode=0o770)

    def open(self,**kwargs):
        """

        :param kwargs:
        :return:
        """
        self._update_from_kwargs(**kwargs)
        self._isOpen = False
        try:
            if self.overwrite:
                if os.path.isfile(self.fullname):
                   os.remove(self.fullname)
        except:
            logger.exception("---> ERROR: can not overwrite report ile: {}".format(self.fullname))
            return false
    
        self._MNE_REPORT = mne.Report(info_fname=self.info_name,title=self.title,image_format=self.image_format,
                                      raw_psd=self.raw_psd,verbose=self.verbose)
        self._isOpen = True
        return self._isOpen

    def save(self,fname=None,overwrite=False):
        if not self.isOpen:
            logger.exception("---> ERROR in saving JuMEG MNE report: {}\n ---> Report not open\n".format(self.fullname))
            return self.isOpen
        
        if fname:
           self.fname = os.path.basename(fname)
           p = os.path.dirame(fname)
           if p:
              self.path=p
       #--- html
        self.MNEreport.save(self.fullname,overwrite=overwrite,open_browser=self.open_browser)
       #--- h5
        if self.write_hdf5:
           self.MNEreport.save(self.fullname.replace(self.extention,".h5"),overwrite=overwrite,open_browser=False)
           logger.info("---> DONE saving JuMEG MNE report: HDF5: {}\n".format(self.fullname))
     
        return self.isOpen
    
    def update_report(self,path=None,flist=None,section=None,prefix=None,replace=True):
        """
        load img from list
        add to report
        :param path   : report image path
        :param flist  : list of pngs
        :param section: section in report e.g.: Noise reducer, ICA
        :param prefix : prefix for caption e.g.: ICA-0815_
        :return:
        """
        fimgs    = []
        captions = []
        
        if not flist: return False
        if not isinstance(flist,(list)):
           flist = list( set( flist ) )
           
        for f in flist:
            fimgs.append( os.path.join(path,f.rstrip()) )
            captions.append( prefix+"-" + os.path.basename(f.rstrip().rsplit(self.image_extention,1)[0]) )
           
        self.MNEreport.add_images_to_section(fimgs,captions=captions,section=section,replace=replace)
        
        if self.verbose:
           logger.info("---> update MNE report: {}\n counts: {} ->\n {}".format(section,len(fimgs),fimgs) )

        return True


class JuMEG_REPORT(JUMEG_SLOTS):
    """
    saving
     noise_reducer fig
     ica figs in HDF
     epocher figs
    
    and show in MNE Reports
    """
    __slots__= {"path","fname","experiment","subject_id","image_config","image_path","_config","_REPORT","_CFG"}
    
    def __init__(self,**kwargs):
        super().__init__()
        self.init()
      
        self._CFG    = jCFG()
        self._REPORT = MNE_REPORT(**kwargs)
        
    @property
    def CFG(self): return self._CFG
    
    @property
    def Report(self): return self._REPORT

    @property
    def verbose(self): return self._REPORT.verbose
    @verbose.setter
    def verbose(self,v):
        self._REPORT.verbose=v

  

def run(self,**kwargs):
    
        """
        jReport.run(path=report_path,
                report_config_file=report_config_file,
                experiment="QUARTERS",subject_id=210857,
                config=config)
        
         open/read cfg /reprt/fname-report.yaml
         MNEreport.open
         
         update NR
         update ICa
         
         save HDf5
         save htlm
        
         report config as dict
         report_path=report_path,path=path,fname=raw_fname,subject_id=210857,config=config
   
         report:
           run: True
           save: True
           overwrite: False

           noise_reducer:
             run: True
           ica:
             run: True

         :param kwargs:
         :return:
        """

        self._update_from_kwargs(**kwargs)
       
       #--- get read report config
        self.CFG.update(config=kwargs.get("image_config") )
        self.CFG.info()
        
        cfg_image = self.CFG.GetDataDict(copy=True)
        
        self.CFG.update(config=kwargs.get("config") )  #config=/report/config file
        cfg = self.CFG.GetDataDict()
      
        self.Report.path      = self.path
        self.Report.fname     = self.experiment + "_" + str( self.subject_id )
        
        self.Report.title     = self.experiment
        self.Report.info_name = "JuMEG Preporcessing"
        if not self.Report.isOpen:
           if not self.Report.open():  return False

        path = jb.expandvars( os.path.dirname(self.image_config) )
        
       #--- noise reducer
        if cfg.get("noise_reducer",False):
           _cfg = cfg_image.get("noise_reducer")
           if _cfg:
              self.Report.update_report(flist=_cfg.get("files"), path=path,section="Noise Reducer",prefix="NR")
       
       #--- ica
        if cfg.get("ica",False):
           _cfg = cfg_image.get("ica")
           if _cfg:
              self.Report.update_report(flist=_cfg.get("files"),path=path,section="ICA",prefix="ICA")
           
        if cfg.get("save",False):
           self.Report.save(overwrite=True)
    
    
def test1():
    #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger)

    stage = "$JUMEG_PATH_LOCAL_DATA/exp/QUATERS/mne"
    fcfg  = os.path.join("/home/fboers/MEGBoers/programs/JuMEG/jumeg-py/jumeg-py-git-fboers/jumeg/pipelines","jumeg_config.yaml")
    
    raw_path  = "210857/QUATERS01/191210_1325/1"
    raw_fname = "210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
  
    report_path  = os.path.join(stage,"report")
    image_path   = os.path.join(stage,raw_path,"report")
    image_config = os.path.join(image_path,raw_fname.rsplit("meeg",1)[0]+"meeg-report.yaml")
    
   #--- read pipeline config
    from jumeg.base.jumeg_base_config import JuMEG_CONFIG_YAML_BASE as jCFG
    CFG = jCFG()
    CFG.update(config=fcfg)
    config = CFG.GetDataDict("report")
   
   #---
    jReport = JuMEG_REPORT()
    jReport.run(path          = report_path,
                experiment    = "QUARTERS",
                subject_id    = 210857,
                image_config  = image_config,
                config        = config)

    raw_path = "210857/QUATERS01/191210_1325/2"
    raw_fname = "210857_QUATERS01_191210_1325_2_c,rfDC,meeg,nr,bcc,int-raw.fif"

    report_path = os.path.join(stage,"report")
    image_path = os.path.join(stage,raw_path,"report")
    image_config = os.path.join(image_path,raw_fname.rsplit("meeg",1)[0] + "meeg-report.yaml")

    jReport.run(path          = report_path,
                experiment    = "QUARTERS",
                subject_id    = 210857,
                image_config  = image_config,
                config        = config)


def test2():
    
   #---
    stage         = "$JUMEG_PATH_LOCAL_DATA/exp/QUATERS/mne"
    raw_path      = "210857/QUATERS01/191210_1325/1"
    raw_fname     = "210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
    report_path   = os.path.join(stage,raw_path,"report")
    report_config = os.path.join(report_path,raw_fname.rsplit("meeg",1)[0]+"meeg-report.yaml")
    
    RP = JuMEG_REPORT()
    
    stage = "$JUMEG_PATH_LOCAL_DATA/exp/QUATERS/mne"
    
    freport = raw_fname.rsplit("_",1)[0] +"-report.yaml"
    
    fpng = "210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr.png"
    cfg  = { "noise_reducer": {"files":[fpng] } }
      
    
   #--- get read report config
    if not RP.CFG.load_cfg(fname=freport):
       RP.CFG.save_cfg(fname=freport,cfg=cfg)
      
    RP.CFG.info()
    RP.CFG.config["test"]={"a":[1,2,3]}
   
  # update(config=cfg )
    RP.CFG.save_cfg(fname=freport)

    RP.CFG.info()
    
if __name__ == "__main__":
  # test1()
   jumeg_logger.setup_script_logging(logger=logger)
   test2()