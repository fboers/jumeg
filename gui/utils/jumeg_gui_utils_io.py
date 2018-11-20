#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 10:08:17 2018

@author: fboers
"""

import os,sys,re,textwrap 
import ast
from types import ModuleType

from glob import glob
import numpy as np

from jumeg.jumeg_base import JuMEG_Base_Basic
jb = JuMEG_Base_Basic()

__version__="v2018-11-13-001"


class JuMEG_UtilsIO_ModuleBase(object):
    """
    
     Paremeters:
     -----------    
      name     : <None>   
      prefix   : <jumeg>  
      fullfile : <None>
      extention: <.py>
      function : <get_args>
      import   : <None>
      
      verbose  : <False>
     
     Example:
     --------
      command/module: my-path/jumeg/jumeg_test01.py     
      name          : jumeg_test01
      fullfile      : my-path/jumeg/jumeg_test01.py
     
      command       : dict of {"name":None,"prefix":"jumeg","fullfile":None,
                               "extention":".py","function":"get_args","package":None}   
    """
    def __init__(self,**kwargs):
        super(JuMEG_UtilsIO_ModuleBase,self).__init__()
        self.__command  = {"name":None,"prefix":"jumeg","fullfile":None,"extention":".py","function":"get_args","package":None} 
        self.__isLoaded = False
        self._update_kwargs(**kwargs)
        
    @property
    def command(self): return self.__command
    
    @property
    def name(self)  : return self.__command["name"]
    @name.setter
    def name(self,v): self.__command["name"]=v
    
    @property
    def module(self)  : return self.__command["name"]
    @module.setter
    def module(self,v): self.__command["name"]=v
   
    @property
    def prefix(self)  : return self.__command["prefix"]
    @prefix.setter
    def prefix(self,v): self.__command["prefix"]=v
   
    @property
    def package(self)    : return self.__command["package"]
    @package.setter
    def pachkage(self,v)  : self.__command["package"]=v
   
    @property
    def fullfile(self)  : return self.__command["fullfile"]
    @fullfile.setter
    def fullfile(self,v): 
        self.__isLoaded = False
        self.__command["fullfile"]=v
    
    @property        
    def function(self)  : return self.__command["function"]
    @function.setter        
    def function(self,v): 
        self.__isLoaded = False
        self.__command["function"]=v
   
    @property        
    def extention(self)  : return self.__command["extention"]
    @extention.setter        
    def extention(self,v): self.__command["extention"]=v
  
    @property
    def import_name(self): return self.prefix +"."+self.name
   
   #----- 
    def update(self,**kwargs):
        self._update_kwargs(**kwargs)
           
    def _update_kwargs(self,**kwargs):
        for k in self.__command.keys():
            self.__command[k] = kwargs.get(k,self.__command[k])
   
    def info(self):
        jb.pp(self.command,head="JuMEG Function Command")

       

class JuMEG_UtilsIO_FunctionFromText(JuMEG_UtilsIO_ModuleBase):
    """
    special issue
    extract a function from a text file e.g. <get_arg> in <jumeg_filter.py>
    and compile it in a new module e.g. for argparser gui
    avoiding/excluding <import>  and imports of dependencies 
    
    Parameters
    -----------       
     name     : <None>   
     prefix   : <jumeg>  
     fullfile : <None>
     extention: <.py>
     function : <get_args>
     import   : <None>
      
     start_pattern: <def >
     stop_pattern : <return >
      
     verbose  : <False>
     
    Example
    -------
     from jumeg.gui.utils.jumeg_gui_utils_io import JuMEG_UtilsIO_FunctionFromText
     JFT          = JuMEG_UtilsIO_FunctionFromText()
     JFT.fullfile = os.environ["JUMEG_PATH"]+"jumeg/filter/jumeg_filter.py"
     JFT.function = "get_args"
     opt,parser   = JFT.apply() 

     parser.print_help()

    """
    def __init__(self,**kwargs):
        super(JuMEG_UtilsIO_FunctionFromText,self).__init__(**kwargs)
        self.__command = {"name":None,"fullfile":None,"extention":".py","function":"get_args","start_pattern":"def","stop_pattern":"return" }
        self.__text     = None
        self.__isLoaded = False
        self._update_kwargs(**kwargs)
   
    @property
    def function_text(self)  : return self.__text
   
    @property
    def isLoaded(self)  : return self.__isLoaded
    
    @property        
    def start_pattern(self)  : return self.__command["start_pattern"]
    @start_pattern.setter        
    def start_pattern(self,v): self.__command["start_pattern"]=v
   
    @property        
    def stop_pattern(self)  : return self.__command["stop_pattern"]
    @stop_pattern.setter        
    def stop_pattern(self,v): self.__command["stop_pattern"]=v
    
    def _open_txt(self):
        """ open module-file (.py) """
        lines = None
        #print("Function File: "+self.fullfile)
        
        with open (self.fullfile,"r+") as farg:
             lines=farg.readlines() 
             farg.close()
        return lines     
     
    def _get_function_code_from_text(self,**kwargs):
        """  extract the function text from module"""
        self._update_kwargs(**kwargs)
        idx = 0
        lines        = None
        l_idx_start  = None
        l_idx_end    = None
        l_intend_pos = None
        self.__text  = None
        
       #--- read in module as txt 
        lines = self._open_txt()
        if not lines : return 
        
       #--- mk mathch pattern 
        find_start_pattern = re.compile(self.start_pattern +'\s+'+ self.function)
       #--- find module start index  
        for l in lines:
            if find_start_pattern.match(l):
               l_idx_start = idx
               breakp
            idx += 1                 
       #--- find intend pos first char
        idx = l_idx_start
        for l in lines[l_idx_start+1:-1]:
            idx += 1
            if not len(l.lstrip() )     :  continue
            if l.lstrip().startswith("#"): continue
            l_intend_pos = len(l) - len(l.lstrip()) # line pos of return
            break
         
       #--- find module end  
        idx = l_idx_start
        for l in lines[l_idx_start+1:-1]:
            idx += 1
            if ( l.find( self.stop_pattern) ) == l_intend_pos:
               l_idx_end=idx
               break
        self.__text = "import sys,os,argparse\n" +''.join( lines[l_idx_start:l_idx_end+1] )
        lines=[]
        return self.__text 

    def _clear(self):
        """
        clear function module space
        """
        self.__isLoaded = False
        
    def load_function(self):
        """
         load function from source code (text file)
         create a new module and execute code
         
         Result
         -------
         return function results
         
        """
        if self.isLoaded: self._clear()    
        self.__isLoaded = False
       
        if not self._get_function_code_from_text(): return
       
        self.__ModuleType = ModuleType(self.function)
        sys.modules[self.function] = self.__ModuleType
        exec( textwrap.dedent( self.function_text), self.__ModuleType.__dict__)
        self.__isLoaded = True
   
    def apply(self):
        """
         if not loaded load function from source code (text file)
         and create a new module and execupte code
         execute function
         
         Result
         -------
         return function results
        """    
        if not self.isLoaded:
           self.load_function()
        if self.isLoaded:  
           # print("OK loaded {}".format(sys.modules[self.function] )) 
           return getattr(self.__ModuleType,self.function)() #opt,parser
                  
        return None
    
       
class JuMEG_UtilsIO_JuMEGModule(object):
    """
    CLS find jumeg modules under jumeg sub folders in PYTHONOATH 
    
    Parameters:
    -----------    
    stage_prefix : jumeg stage start of jumeg directory : <jumeg> 
    prefix       : file prefix     <None>
    postfix      : file postfix    <None>
    extention    : file extention  <".py>
    permission   : file permission <os.X_OK|os.R_OK>
    function     : function name in module <get_args>
    
    Results:
    --------
    list of executable modules with fuction < get_args> in jumeg PYTHONPATH
        
    """ 
    def __init__(self,stage_prefix="jumeg",prefix="jumeg",postfix=None,extention=".py",permission=os.X_OK|os.R_OK,function="get_args",**kwargs):  
        super(JuMEG_UtilsIO_JuMEGModule, self).__init__(**kwargs)
        #super().__init__()
        
        self.stage_prefix  = stage_prefix
        self.prefix        = prefix
        self.postfix       = postfix
        self.extention     = extention
        self.permission    = permission
        self.function      = function
        self.skip_dir_list = ["old","gui","wx"]
        self._module_list  = [] 
        self._jumeg_path_list=[]   
        
    @property
    def module_list(self): return self._module_list
    @property
    def jumeg_path_list(self): return self._jumeg_path_list  
    
    def PathListItem(self,idx):
        return os.path.split( self.module_list[idx] )[0]
  
    def _is_function_in_module(self,fmodule,function=None):
        """
        https://stackoverflow.com/questions/45684307/get-source-script-details-similar-to-inspect-getmembers-without-importing-the
   
        """
        if function:
           self.function=function
        if not self.function: return  
        
        try:
            mtxt = open(fmodule).read()
            tree = ast.parse(mtxt)
            for fct in tree.body:
                if isinstance( fct,(ast.FunctionDef)):
                   if fct.name == self.function:
                      return True
        except:
            pass
        
    def get_jumeg_path_list_from_pythonpath(self):
        """ jumeg """
       
        self._jumeg_path_list=[]
        l=[]
        for d in os.environ["PYTHONPATH"].split(":"):
            if os.environ.get(d):
               d = os.environ.get(d)
            if d == ".":
               d = os.getcwd() 
            if os.path.isdir( d + "/" + self.stage_prefix):
               l.append( d + "/" + self.stage_prefix )
    
        self._jumeg_path_list = list( set(l) ) # exclude double
        self._jumeg_path_list.sort()
        return self._jumeg_path_list 
        
    
    def ModuleListItem(self,idx):
        """  jumeg.my subdirs.<jumeg_function name>"""
      
        if not len(self.module_list): return
        p,f = os.path.split( self.module_list[idx])
        m = p.split("/"+self.stage_prefix + "/")[-1] + "/" + os.path.splitext(f)[0]
        return m.replace("/",".")
    
    def ModuleFileName(self,idx):
        """ 
        Parameters:
        -----------
        index
        """
        return self._module_list[idx]
    
    def ModuleNames(self,idx=None):
        """
        get module name from file list
        Parameters:
        -----------
        idx: if defined return only this filename from list <None>
             else return list of filenames
        """   
        if jb.is_number(idx):
           return os.path.basename( self._module_list[idx] ).replace(self.extention,"")
        l=[]
        for f in self.module_list:
            l.append(os.path.basename(f).replace(self.extention,""))
        return l    
           
        #--- get_path_and_file
        # p,f=os.path.split( self.file_list[idx] )
    def FindModules(self,**kwargs):
        """
        find modules /commands under jumeg with defined permissions
        
        Parameters:
        -----------    
        stage_prefix: <jumeg">
        prefix      : <jumeg>
        postfix     : <None>
        extention   : <.py> 
        permission  : <os.X_OK|os.R_OK>
        function    : <get_args>
      
        Results:
        ---------
        list of module names 
        """
        self._walk(**kwargs)
        return self.ModuleNames()
    
    def update(self,**kwargs):
        """ """
        self.stage_prefix = kwargs.get("stage_prefix",self.stage_prefix)
        self.prefix       = kwargs.get("prefix",self.prefix)
        self.postfix      = kwargs.get("postfix",self.postfix)
        self.extention    = kwargs.get("extention",self.extention)
        self.permission   = kwargs.get("permission",self.permission)
        self.function     = kwargs.get("function",self.function)
        self._module_list = [] 
        self._jumeg_path_list = self.get_jumeg_path_list_from_pythonpath()
               
    def _walk(self,**kwargs):  
        """
        search recursive for executable modules
        
        Parameters:
        -----------
        stage_prefix : stage prefix <jumeg>
        prefix    : file prefix     <jumeg>
        postfix   : file postfix    <None>
        extention : file extention  <".py>
        permission: file permission <os.X_OK|os.R_OK>
            
        Results:
        --------     
        list of executable modules, full filename
        """
        self.update(**kwargs)
         
        skip_dir_set = set(self.skip_dir_list)
        for p in  ( self._jumeg_path_list ):
            for root, dirs, files in os.walk(p):
                if (set(root.split(os.sep)) & skip_dir_set): continue
                for f in files:
                    if self.prefix:
                       if not f.startswith(self.prefix): continue
                    if self.extention:
                       if not f.endswith(self.extention): continue
                    if os.access(root+"/"+f,self.permission): 
                       fmodule = os.path.join(root,f)
                       if self._is_function_in_module(fmodule):
                          self._module_list.append(fmodule) 
                     
        self._module_list.sort()
        return self._module_list
    
  
 #get_path_and_fiel
 #a,b=os.path.split()

class JuMEG_UtilsIO_Id(object):
    """
     CLS find IDs in <stage> 
     for mne [meg] data or eeg along directory structure:
     <stage/mne>   <stage/eeg>
     
    """ 
    
    def __init__(self,stage=None,data_type='mne'):
        super(JuMEG_UtilsIO_Id, self).__init__()
        self._stage      = None
        self.stage       = stage
        self.data_type   = data_type
        self.found_list  = []             
        self.pdfs        = dict() 

    @property
    def stage(self): return self._stage
    @stage.setter
    def stage(self,v):
        if v:
           self._stage = os.path.expandvars( os.path.expanduser(v) )

    def __get_path(self):
        jb.logger.error(self.stage)
        try:
            if not self.stage.endswith(self.data_type):
               return self.stage+"/"+self.data_type
            return self.stage

        except Exception as e:
            msg="No such file or directory or not defined: <data_type>:{} <stage>: {}".format(self.data_type,self.stage)
            jb.print_error(msg+"\n"+str(e),head="JuMEG_UtilsIO_Id.path")
            jb.logger.error(e.args)
            return None

    path = property(__get_path)             

    def update(self,data_type=None,scan=None):
        """
        update data type and call update for eeg  or meg
        
        Parameters:
        -----------
        data_type: meg or eeg   <None>
        scan     : name of scan <None>
        
        Results:
        --------    
        file list
        """
        if data_type:
           self.data_type = data_type
        if self.data_type == 'mne':
           return self.update_mne(scan=scan)
        if self.data_type == 'eeg':
            return self.update_eeg()    
    
    def update_mne(self,path=None,scan=None): 
        """
        update meg file list
        Parameters:
        -----------
        sacn: name of scan <None>
        
        Results:
        --------    
        file list
        """
        self.found_list = []
        if path:
           self.path = path

        if not self.path: return
        p = self.path
        if not os.path.isdir(p):
           jb.print_error("ERROR in <JuMEG_UtilsIO_Id.update_mne> No directory: {}".format(p))
           return None
       
        for f in os.listdir(p):
            if os.path.isdir(p+"/"+f ):
               if f.isdigit(): 
                  if scan:
                     if os.path.isdir(p+"/"+f+"/"+scan ):
                        self.found_list.append(f)
                  else:   
                     self.found_list.append(f)
        self.found_list.sort()         
        return self.found_list
    
    def update_eeg(self): 
        """
        update eeg file list
        
        Results:
        --------    
        file list
        """
        self.found_list = []
        if not self.path: return
        p = self.path
        if not os.path.isdir(p):
           print("ERROR in <update_meg_ids> NO directory: {}".format(p))
           return None
       
        for f in os.listdir(p):
            if os.path.isdir(p+"/"+f ):
               if f.isdigit():
                  self.found_list.append(f)  
                 
        self.found_list.sort()
         
        return self.found_list
 
   
         
class JuMEG_UtilsIO_PDFPattern(object):
    """ 
    Base CLS to find PosteddataFiles (MEG or EEG files) via pattern 
    
    Parameters:
    -----------    
    prefix     : <'*'>
    postfix_meg: <'*c,rfDC-raw.fif'>
    postfix_eeg: <'*.vhdr'>
    id         : <None>
    scan       : <None>
    session    : <None>
    run        : <None>
    data_type  : <'mne'>
    
    """
    def __init__(self,prefix='*',postfix_meg='*c,rfDC-raw.fif',postfix_eeg='*.vhdr',id=None,scan=None,session=None,run=None,data_type='mne'):  
        super(JuMEG_UtilsIO_PDFPattern, self).__init__() 
               
        self._number_of_pdfs = {'mne':0,'eeg':0}
        self.verbose         = False
        self._pdf={'id':id,'scan':scan,'session':session,'run':run,'postfix_meg':postfix_meg,'postfix_eeg':postfix_eeg,'prefix':prefix,'data_type':data_type,
                   'pattern':None,'seperator':'_','data_type_mne':'mne','data_type_eeg':'eeg'   
                  }       
        
    def _update(self,stage=None,id=None,scan=None,session=None,run=None,postfix=None,postfix_meg=None,postfix_eeg=None,prefix=None,data_type=None):
        """ """
        if stage:
           self.stage = stage
        if data_type: # mne / eeg
           self.data_type = data_type  
        if id:
           self.id = id
        if scan:
           self.scan = scan
        if session:
           self.session = session
        if run:
           self.run = run
        
        if postfix:
           self.postfix = postfix
        if postfix_meg:
           self.postfix_meg = postfix_meg
        if postfix_eeg:
           self.postfix_eeg = postfix_eeg
           
        if prefix:
           self.prefix = prefix
            
    def update_pattern(self,*args,**kwargs):
        """ """
        self._update(*args,**kwargs)
            
        l=[]
        if self.id:
           l.append(self.id)
        if self.scan:
           l.append(self.scan)
        if self.session:
           l.append(self.session)
        if self.run:
           l.append(self.run)
        if len(l):
           l.append(self.postfix) 
           self.pattern = self.prefix+self.seperator.join(l)
        else:
           self.pattern = self.postfix
        return self.pattern
  #---    
    @property
    def number_of_pdfs(self):     return self._number_of_pdfs[self.data_type]
  #--- 
    @property
    def number_of_pdfs_mne(self): return self._number_of_pdfs['mne']
  #---
    @property
    def number_of_pdfs_eeg(self): return self._number_of_pdfs['eeg']
  #--- 
    @property
    def data_type(self):  return self._pdf['data_type']
    @data_type.setter
    def data_type(self,v): self._pdf['data_type']=v  
  #---  
    @property
    def data_type_mne(self):  return self._pdf['data_type_mne']
    @data_type_mne.setter
    def data_type_mne(self,v): self._pdf['data_type_mne']=v  
  #---  
    @property
    def data_type_eeg(self):  return self._pdf['data_type_eeg']
    @data_type_eeg.setter
    def data_type_eeg(self,v): self._pdf['data_type_eeg']=v      
  #---  
    @property
    def pattern(self):  return self._pdf['pattern']
    @pattern.setter
    def pattern(self,v): self._pdf['pattern']=v  
  #---        
    @property
    def seperator(self): return self._pdf['seperator']
    @seperator.setter
    def seperator(self,v): self._pdf['seperator']=v    
  #---  
    @property
    def id(self): return self._pdf['id']
    @id.setter
    def id(self,v): self._pdf['id']=v    
  #---   
    @property
    def scan(self): return self._pdf['scan']
    @scan.setter
    def scan(self,v): self._pdf['scan']=v    
  #---        
    @property
    def session(self): return self._pdf['session']
    @session.setter
    def session(self,v): self._pdf['session']=v  
  #---       
    @property
    def run(self): return self._pdf['run']
    @run.setter
    def run(self,v): self._pdf['run']=v    
  #---    
    @property
    def data_type(self): return self._pdf['data_type']
    @data_type.setter
    def data_type(self,v): self._pdf['data_type']=v    
  #---  
    @property
    def prefix(self): return self._pdf['prefix']
    @prefix.setter
    def prefix(self,v):  self._pdf['prefix']=v    
  #---    
    @property
    def postfix_meg(self):   return self._pdf['postfix_meg']
    @postfix_meg.setter
    def postfix_meg(self,v): self._pdf['postfix_meg']=v      
  #---    
    @property
    def postfix_eeg(self):   return self._pdf['postfix_eeg']
    @postfix_eeg.setter
    def postfix_eeg(self,v): self._pdf['postfix_eeg']=v 
  #---    
    @property
    def postfix(self):
        if self.data_type =='mne':
           return self.postfix_meg
        return self.postfix_eeg
    @postfix.setter
    def postfix(self,v):
        if self.data_type =='mne':
           self.postfix_meg=v
        else: 
           self.postfix_eeg=v      
  #---     
    @property
    def path(self):
        if not self.stage.endswith(self.data_type):
           return self.stage+"/"+self.data_type
        return self.stage         
    
    
class JuMEG_UtilsIO_PDFs(JuMEG_UtilsIO_PDFPattern):
    """
     CLS find IDs in <stage> 
     for mne [meg] data or eeg along directory structure:
     <stage/mne>   <stage/eeg>
     
    """     
    def __init__(self,stage='.', data_type='mne',experiment=None,scan=None,**kwargs):  
        super(JuMEG_UtilsIO_PDFs, self).__init__(data_type=data_type,scan=scan,**kwargs)
        self.stage       = stage
        self.experiment  = experiment
        #self.type        = data_type
        self.id_list     = []    
        self.pdfs        = dict()
        
        self.__NO_MATCH  = -1
        #self.scan        = scan
        #self.data_type   = data_type
        #self.pattern     = JuMEG_UtilsIO_PDFPattern()  
        
    def update(self,id_list=None,stage=None,scan=None,session=None,run=None,postfix_meg=None,postfix_eeg=None): 
        """
        for each id in id-list find mne/meg and eeg data
        Parameter:
        ----------
         parameter to change is defined

         id_list: <None>
         stage  : <None>
         scan   : <None>
         session: <None>
         run    : <None>
         postfix_meg: <None>
         postfix_eeg: <None>

        Result:
        -------
        pdf dictionary

        """
        
        self.id_list = []
        if isinstance(id_list,(list)):
           self.id_list = id_list
        elif id_list:
           self.id_list.append( id_list ) 
        
        self._update(stage=stage,scan=scan,session=session,run=run,postfix_meg=postfix_meg,postfix_eeg=postfix_eeg)   
        
        self._update_data_type(data_type=self.data_type_mne)
   
        self._update_data_type(data_type=self.data_type_eeg)
        
        
      #--- search for matching scan and run  
        for id_item in self.pdfs[ self.data_type_mne ]:
            n_raw = len( self.pdfs[ self.data_type_mne ][id_item]['raw'] )
          #--- make lookup tab for matching later mne raw with eeg raw   
            self.pdfs[ self.data_type_mne ][id_item]['eeg_idx'] = np.zeros( n_raw,dtype=np.int64 ) + self.__NO_MATCH
            
            if id_item in self.pdfs[ self.data_type_eeg ]:
               eeg_index = self._match_meg_eeg_list(meg_list=self.pdfs[ self.data_type_mne ][id_item]['raw'],
                                                    eeg_list=self.pdfs[ self.data_type_eeg ][id_item]['raw'])
            else:
               eeg_index = np.zeros( n_raw,dtype=np.int64 ) + self.__NO_MATCH

        #--- ck for double                  
            uitems,uidx,uinv = np.unique(eeg_index,return_inverse=True,return_index=True)
            self.pdfs[self.data_type_mne][id_item]['eeg_idx'][uidx] = uitems
                   
        return self.pdfs 

    def _match_meg_eeg_list(self,meg_list=None,eeg_list=None):
        """
         find common eeg & meg files from meg and eeg list

         Parameter:
         ----------
         meg_list: <None>
         eeg_list: <None>

         Result:
         --------
         numpy array: matching index for eeg list; -1 => no match

         Example:
         --------
         type of input data

          MNE/MEG
           path to data/205630/INTEXT01/181017_1006/1/205630_INTEXT01_181017_1006_1_c,rfDC-raw.fif
           path to data/205630/INTEXT01/181017_1006/2/205630_INTEXT01_181017_1006_2_c,rfDC-raw.fif
           ...
           path to data/205630/INTEXT01/181017_1112/1/205630_INTEXT01_181017_1112_1_c,rfDC-raw.fif
           path to data/205630/INTEXT01/181017_1112/2/205630_INTEXT01_181017_1112_2_c,rfDC-raw.fif
           path to data/205630/INTEXT01/181017_1135/1/205630_INTEXT01_181017_1135_1_c,rfDC-raw.fif
          EEG
           path to data/205630_INTEXT01_181017_1006.02.vhdr
           path to data/205630_INTEXT01_181017_1006.01.vhdr
           ...
           path to data/205630_INTEXT01_181017_1112.01.vhdr
           path to data/205630_INTEXT01_181017_1112.02.vhdr

          or older experiments
             meg: path to data/204260_MEG9_130619_1301_2_c,rfDC-raw.fif
             eeg: path to data/204260_MEG9_2.vhdr
         """


        found_list = np.zeros( len(meg_list),dtype=np.int64 ) + self.__NO_MATCH
        match_run  = True
        match_time = False
        match_date = False
        n    = len( os.path.basename(eeg_list[0]).replace('.', '_').split('_') )
        eeg_idx0 = 2

        if n == 6:
           match_date = True
           match_time = True
           eeg_idx1 = 5
        elif n == 5:
           match_date = True
           eeg_idx1 = 4
        else:
           eeg_idx1 = 3

        eeg_pattern = np.zeros( (len(eeg_list),eeg_idx1 - 2), dtype=np.int)

        idx = 0
        for feeg in eeg_list:
            s = os.path.basename(feeg).replace('.', '_').split('_')
            eeg_pattern[idx][:] = np.array(s[ eeg_idx0:eeg_idx1 ], dtype=np.int)
            idx+=1

        idx = 0
        for fmeg in meg_list:
            idxs = None
            f = os.path.basename(fmeg)
            meg_pattern = np.array(f.replace('.', '_').split('_')[2:5],dtype=np.int)
          #--- match run
            if match_run:
               idxs = np.where(eeg_pattern[:,-1]== meg_pattern[-1])[0]
               if not idxs.size: continue
          #--- match time
            if match_time:
               found_idxs = np.where(eeg_pattern[idxs, -2] == meg_pattern[-2])[0]
               if not found_idxs.size: continue
               idxs = idxs[found_idxs]
         # --- match date
            if match_date:
               found_idxs = np.where(eeg_pattern[idxs, -3] == meg_pattern[-3])[0]
               if not found_idxs.size: continue
               idxs = idxs[found_idxs]

            if isinstance(idxs,(np.ndarray)):
               if idxs.size:
                  found_list[idx]=idxs[0]

            idx+=1
        return found_list

    
    def _update_data_type(self,data_type=None): 
        """ """
        data_path = self.stage+'/'+data_type
        
        pdfs   = dict()
        n_pdfs = 0
        
        for id_item in self.id_list:
            pattern = self.update_pattern(id=id_item,data_type=data_type)
            if self.verbose:
               print("---> JuMEG_UtilsIO_PDFs._update_data_type:")
               print(" --> Search     : {} -> {}".format(id_item,self.scan))
               print("  -> data type  : {}".format(data_type))
               print("  -> pattern    : {}".format(pattern))
               print("  -> data path  : {}\n".format(data_path))
          #--- https://stackoverflow.com/questions/18394147/recursive-sub-folder-search-and-return-files-in-a-list-python
            r=[y for x in os.walk(data_path) for y in glob(os.path.join(x[0], pattern))]
            if r :
               pdfs[id_item] = dict()
               pdfs[id_item]['path']    = [ os.path.dirname(raw)  for raw in sorted(r) ]
               pdfs[id_item]['raw']     = [ os.path.basename(raw) for raw in sorted(r) ]
              
               n_pdfs += len (pdfs[id_item]['raw'])
               
        self.pdfs[data_type] = pdfs
                   
        self._number_of_pdfs[data_type] = n_pdfs      
        return self.pdfs,n_pdfs
           
           
          
    