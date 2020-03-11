#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors:
# Lukas Kurth <l.kurth@fz-juelich.de>
# Frank Boers <f.boers@fz-juelich.de>,
#
#-------------------------------------------- 
# Date: 10.03.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

"""
https://stackoverflow.com/questions/6866600/how-to-parse-read-a-yaml-file-into-a-python-object
"""
import os,os.path as op
import logging,pprint

from jumeg.base.jumeg_base import jumeg_base as jb
from jumeg.base            import jumeg_logger

import datetime
import getpass
from copy import copy
try:
   from ruamel.yaml import YAML
   yaml = YAML()
   yaml.indent(mapping=2, sequence=3, offset=3)
except:
   import yaml
   
import json

try:
   logger = logging.getLogger("jumeg")
   logger.setLevel("INFO")
except:
   logger = logging.getLogger()
   

__version__= "2020.03.11.01" #datetime.datetime.now()

class _Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

class dict2obj(dict):
    '''
    parses a dict to a Python Object
    '''
    def __init__(self, dict_):
        super(dict2obj, self).__init__(dict_)
        for key in self:
            item = self[key]
            if isinstance(item, list):
                for idx, it in enumerate(item):
                    if isinstance(it, dict):
                        item[idx] = dict2obj(it)
            elif isinstance(item, dict):
                self[key] = dict2obj(item)

    def __getattr__(self, key):
        # Enhanced to handle key not found.
        if self.has_key(key):
            return self[key]
        else:
            return None

class Struct(object):
    """
    https://stackoverflow.com/questions/1305532/convert-nested-python-dict-to-object
    Nr: 30
    """
    def __init__(self, data):
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return Struct(value) if isinstance(value, dict) else value
        

class JuMEG_CONFIG_Info():
    
    def __init__(self,user=None,date=None,version=None,comments=None):
        self._param={"user":None,"date":None,"version":version,"comments":comments}
        if user==None:
            user=getpass.getuser()
            self._param["user"]=user
        else:
            self._param["user"]=user
        if date!=None:
            self._param["date"]=date
        
    def reload_date(self):
        '''returns the actual date and time'''
        now=datetime.datetime.now()
        dt=now.strftime('%Y-%m-%d')+" "+now.strftime('%H:%M')
        return dt
        
    def info(self):
        msg = ["---> Config Info:"]
        for k in ["user","date","version","comments"]:
            msg.append("  -> {} : {}".format(k,self._param[k]) )
        logger.info( "\n".join(msg) )
        
        
    def get_param(self):
        d=copy(self._param)
        d["date"]=self.date
        return d
    
    def _get_param(self,key):
        return self._param[key]
    
    def _set_param(self,key,value):
       if key in self._param.keys():
          self._param[key]=value
        
    @property
    def user(self): return self._get_param("user")
    
    @property
    def date(self):
        if self._param["date"]==None:
            return self.reload_date()
        return self._get_param("date")
        
    @property
    def version(self): return self._get_param("version")
    
    @version.setter
    def version(self,v): self._set_param("version",v)
    
    @property
    def comments(self): return self._get_param("comments")
    
    @comments.setter
    def comments(self,v): self._set_param("comments",v)
        
        
class JuMEG_CONFIG(object):
    '''
    load or get yaml config as dict
    convert to object
    
    Example:
    --------
    
    from jumeg.base import jumeg_logger
    from jumeg.base.jumeg_base_config  import JuMEG_CONFIG as jCFG
    jumeg_logger.setup_script_logging()
    
    CFG  = jCFG()
    fcfg = "test.yaml"
    cfg  = { "noise_reducer": {"files":["test.png"] } }
    
    #--- load config
    if CFG.load_cfg(fname=fcfg):
       CFG.save_cfg(fname=fcfg,data=cfg)
     
    CFG.info()
    CFG.config["test"]={"a":[1,2,3]}
    CFG.save_cfg(fname=fcfg)
    CFG.info()
    
    '''
    def __init__(self,**kwargs):
        self._fname    = None
        self._data     = None
        self._cfg      = {}
        self.useStruct = False
        self.verbose   = kwargs.get("verbose",False)
        
        self._init(**kwargs)
        self._yaml=YAML()
    
    @property
    def config(self): return self._cfg
  
    @property
    def data(self): return self._data
    
    @property
    def fname(self): return self._fname
    
    @fname.setter
    def fname(self,v):
       self._fname=jb.expandvars(v)
   
    @property
    def filename(self): return self._fname
    
    def _init(self,**kwargs):
        pass
    
    def info(self):
        logger.info("---> config info:\n  -> file: {}\n{}\n".format(self.filename,pprint.pformat(self._cfg,indent=4)))
        
    def GetDataDict(self,key=None):
        '''
        returns the dict or one element of the dict
        :param key: key of the returned part
        :type key: str
        '''
        if key:
           return self._cfg.get(key)
        return self._cfg
    
    def _update_struct(self):
        self._data = None
        if self.useStruct:
           self._data = Struct( self._cfg )
           return self._data
        return self._cfg
        
    def load_cfg(self,**kwargs):
        '''
        returns the data extracted from a .yaml config file
        :param fname: filename
        :type fname: str
        :param key: key of the returned part
        :type key: str
        :param useStruct: <False> return cfg as struct/obj  e.g.: cfg["ica"]["run"] => cfg.ica.run
        '''
        self.fname = kwargs.get("fname",self.fname)
        if not self.fname:
           return None
        if not os.path.isfile(self.fname):
           return None
       
        self._cfg = {}
        self._data= None
        self.useStruct = kwargs.get("useStruct",self.useStruct)
        
        with open(self.fname) as FH:

            if self.fname.endswith(".yaml"):
               self._cfg = yaml.load( FH )
            elif fname.endswith(".json"):
               self._cfg = json.load( FH )

        if kwargs.get("key",None):
           self._cfg = self._cfg.get( kwargs["key"] )
        
        if self.verbose:
           logger.info( " --> done loading config file: {}".format(self.fname) )
        return self._update_struct()
        
    def update(self,**kwargs):
        '''
        update config obj
        :param config: config dict or filename
        :type config: dict or str
        :param key: if <key> use part of config e.g.: config.get(key)
        :type key: str
        '''
        cfg = kwargs.get("config",None)
        key = kwargs.get("key",None)
        
        self.useStruct = kwargs.get("useStruct",self.useStruct)
        
        if isinstance(cfg,(dict)):
           if key:
              self._cfg = cfg.get(key)
           self._fname = None
           return self._update_struct()
        
        return self.load_cfg(fname=cfg,key=key)
           
    def save_cfg(self,fname=None,data=None):
         '''
         saves the data into new configfile or
         overwrites existing file with the filename <fname>
         and updates <fname> in class
         
         :param fname: the filename the data will be saved in
         :type fname: str
         :param data: the data which will be written into the file
         :type data: dict
         '''
         if data:
            self._cfg  = data
            self._update_struct()
        
         if fname:
            self.fname = fname
         with open(self.fname, "w") as FH:
             if fname.endswith(".yaml"):
                yaml.dump(self._cfg,FH)
             elif fname.endswith(".json"):
                json.dump(self._cfg,FH)
             else:
                logger.exception(" ERROR config file name must end with [.yaml | .json]: {}".format(self.fname))
         if self.verbose:
            logger.info( " --> done saving config file: {}".format(self.fname) )
            
if __name__=='__main__':
    from jumeg.base.jumeg_logger import setup_script_logging
    logger=setup_script_logging(logger=logger,name="jumeg",opt=None)
    info=JuMEG_CONFIG_Info(version=__version__)
    info.printInfo()
