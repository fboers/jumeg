"""
Created on Thu March 15:03:2017
@author: fboers
      
   
"""
import os,sys
import numpy as np

import mne
from jumeg.jumeg_base import JuMEG_Base_IO

__version__='v2017-03-15-001'

#----------------------------------------------------------------------------------------
class JuMEG_TSV_IO_DATA(JuMEG_Base_IO):
      """
       data I/O : update/load fif file
      """
      def __init__(self, fname=None,path=None,raw=None,experiment=None,bads=None,verbose=None):
          
          super(JuMEG_TSV_IO_DATA, self).__init__()

          self.verbose    = verbose
          self.fname      = fname
          self.path       = path
          self.raw        = raw
          self.experiment = experiment
          self.bads       = bads
          self.append_bads= True

          self.dtype_original = None
          self.dtype_plot     = np.float32

          self.raw_is_loaded  = False
        
      def update(self,path=None,fname=None,raw=None,reload=False):
         
         #--- reload
          if (reload and self.raw_is_loaded):
             fname    = self.get_fif_name(self,raw=self.raw,extention=".fif")
             self.raw = None
             raw = None
         #---
          self.raw_is_loaded = False
         #---                
          self.raw,fname = self.get_raw_obj(fname,raw=raw,path=path)
              
          if self.raw:          
             self.fname           = fname
             self.dtype_original  = self.raw._data.dtype
             self.bads            = self.picks.bads(self.raw)
             self.raw_is_loaded   = True
             # return self.raw,self.bads

          if fname:
             self.path  = os.path.dirname(  fname )
             self.fname = os.path.basename( fname )
          if not self.path:
                 self.path ="."+ os.path.sep
          elif not os.path.exists(self.path):
                 self.path ="."+ os.path.sep
                 print "JuMEG TSV IO error: path not exist: " + self.path
          if self.verbose:
             print"-"*40
             print"---> TSV IO Data -> update"
             print"  -> file: " + self.fname
             print"  -> path: " + self.path
             print"-"*40
             print"  -> Info"
             print self.raw.info
             print"-"*40
             
          # self.update_channel_info()
 

      def save_bads(self):
          return self.update_bad_channels(raw=self.raw,bads=self.bads,append=self.append_bads,save=True)

     