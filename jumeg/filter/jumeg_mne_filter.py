#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 12.12.19
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import mne
import logging
import numpy as np
from jumeg.base.jumeg_base import jumeg_base as jb

logger = logging.getLogger("jumeg")

__version__= "2019.12.12.001"

class JuMEG_MNE_FILTER():
    """
    wrapper cls to wrap mne.filter in juMEG
     call MNE filter e.g.:
              raw.filter(l_freq=flow,h_freq=fhigh,picks=picks)
        
    save and rename filterd raw file
    
    
    raw      : <None> raw obj
    flow     : <None> mne <l_freq>
    fhigh    : <None> mne <h_freq>
    picks    : <None> => if None then exclude channels from <stim> group
    save     : <False> / True
    overwrite: <False> if save overwrite existing filtered file
    verbose  : <False> tell me more
    debug    : <False>
    postfix  : <None>  postfix for filename
    
    Returns:
    --------
    filename of filtered raw
    !!! raw is filtered in place !!!
    
    Example:
    --------
    from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER
   #--- load raw
    raw = raw_fname = jb.get_raw_obj(fname,raw=None)
  
   #--- ini MNE_Filter class
    jfi= JuMEG_MNE_FILTER()
  
   #--- filter inplace
    fname_fitered_raw = jfi.apply(raw=raw,flow=0.1,fhigh=45.0,picks=None,save=True,verbose=True,overwrite=True)
    
    """
    __slots__ = ["raw","flow","fhigh","picks","save","overwrite","verbose","debug","_is_filtered","_is_reloaded"]
    
    def __init__(self,**kwargs):
        #super().__init__()
        
        self.clear()
        
        self._update_from_kwargs(**kwargs)
    
    @property
    def fname(self):
        return jb.get_raw_filename(self.raw,index=0)
    
    @property
    def isFiltered(self):
        return self._is_filtered
    
    @property
    def isReloaded(self):
        return self._is_reloaded
    
    def clear(self):
        for k in self.__slots__:
            self.__setattr__(k,None)
    
    def _update_from_kwargs(self,**kwargs):
        for k in self.__slots__:
            self.__setattr__(k,kwargs.get(k,self.__getattribute__(k)))
    
    def _update_postfix(self,**kwargs):
        """return filter extention """
        self._update_from_kwargs(**kwargs)
        fi_fix = None
        
        if self.flow and self.fhigh:
            fi_fix = "fibp"
            fi_fix += "%0.2f-%0.1f" % (self.flow,self.fhigh)
        elif self.flow:
            fi_fix = "fihp"
            fi_fix += "%0.2f" % self.flow
        elif self.fhigh:
            fi_fix = "filp"
            fi_fix += "%0.2f" % (self.fhigh)
        
        # self.postfix = fi_fix
        return fi_fix

    @property
    def postfix(self): return self._update_postfix()

    def apply(self,**kwargs):
        """
        :param kwargs:
         flow,fhigh,raw,picks
         filter raw in place
         call MNE filter e.g.:
              raw.filter(l_freq=flow,h_freq=fhigh,picks=picks)
        :return:
         fname

        """
        
        self._update_from_kwargs(**kwargs)
        self._is_filtered = False
        self._is_reloaded = False
        
        v = jb.verbose
        jb.verbose = self.verbose
        
        logger.info("---> Filter start: {}".format(self.fname))
        
        self._update_postfix()
        fname,ext = self.fname.rsplit('-',1)  #raw.fif'
        fname += "," + self.postfix + "-" + ext
        
        #--- ck if load from disk
        if not self.overwrite:
            if jb.isFile(fname):
                logger.debug("  -> Filter reloading from disk ...")
                self.raw,fname = jb.get_raw_obj(fname,None)
                self._is_filtered = True
                self._is_reloaded = True
        
        if not self._is_filtered:
            logger.info("  -> Filter start MNE filter ...")
            if isinstance(self.picks,(list,np.ndarray)):
               picks = self.picks
            else:
               logger.warning("---> picks not defined : excluding channel group <stim> and <resp>")
               picks = jb.picks.exclude_trigger(self.raw)
               
            self.raw.filter(l_freq=self.flow,h_freq=self.fhigh,picks=picks)
            self._is_filtered = True
            
            if self.save:
                logger.info("  -> Filter saving data")
                fname = jb.apply_save_mne_data(self.raw,fname=fname,overwrite=True)
            else:
                jb.set_raw_filename(self.raw,fname)
        
        logger.info("---> Filter done: {}\n".format(self.fname) +
                    "  -> reloaded from disk: {}".format(self._is_reloaded)
                    )
        
        jb.verbose = v
        return fname
    
    def GetInfo(self,msg=None):
        """

        :param msg:
        :return:
        """
        _msg = ["---> Filter      : {}".format(self.isFiltered),
                " --> raw filtered: {}".format(self.fname),
                "  -> prefix: {}".format(self.postfix),
                "  -> flow  : {}".format(self.flow),
                "  -> fhigh : {}".format(self.fhigh),
                "  -> save  : {}".format(self.save)
                ]
        if self.debug:
           _msg.extend(["-"*20,
                        "->  MNE version: {}".format(mne.__version__),
                        "->      version: {}".format(__version__) ])
        if msg:
            msg.extend(_msg)
            return msg
        else:
            logger.info(_msg)



#---
def jumeg_mne_filter(raw=None,fname=None,**kwargs):
    jfi   = JuMEG_MNE_FILTER(raw=raw,fname=fname)
    fname = jfi.apply(**kwargs)
    return raw,fname
    
#if cfg.post_filter.run:
#   self.PostFilter.apply(
#                         flow  = cfg.post_filter.flow,
#                         fhigh = cfg.post_filter.fhigh,
#                         save  = cfg.post_filter.save,
#                         raw   = raw_unfiltered_clean, # ????
#                         picks = jb.picks.exclude_trigger(raw_filtered_clean)
#                       )
# return self.PostFilter.raw

    
    