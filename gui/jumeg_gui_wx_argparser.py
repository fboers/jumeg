#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
JuMEG Gui argparser
selects an executable <jumeg_xyz.py> script from list
start them with chosen parameters
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de>
#
#--------------------------------------------
# Date: 21.11.18
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,sys,argparse
import warnings
import wx

from wx.lib.pubsub import pub
from wx.lib.scrolledpanel import ScrolledPanel

from jumeg.jumeg_base                                     import jumeg_base as jb
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_frame           import JuMEG_MainFrame
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_panel           import JuMEG_wxMainPanel

from jumeg.gui.wxlib.jumeg_gui_wxlib_pbshost              import JuMEG_wxPBSHosts
from jumeg.gui.wxlib.jumeg_gui_wxlib_logger               import JuMEG_wxLogger
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxControlButtonPanel,JuMEG_wxControls,JuMEG_wxControlIoDLGButtons,JuMEG_wxControlGrid,JuMEG_wxSplitterWindow

from jumeg.ioutils.jumeg_ioutils_function_parser          import JuMEG_IoUtils_FunctionParser,JuMEG_IoUtils_FunctionParserBase,JuMEG_IoUtils_JuMEGModule
from jumeg.ioutils.jumeg_ioutils_subprocess               import JuMEG_IoUtils_SubProcess

__version__='2018-11-18.001'


class JuMEG_ArgParserBase(JuMEG_IoUtils_FunctionParserBase):
    """
    JuMEG_ArgParser
    import <function> from a script/module and
    get program arguments [parser.parse_args(), parser ] form this function
    the function should return < parser.parse_args() > and  < parser > obj from < argparse.ArgumentParser >
        
    Parameters:
    -----------
      module  : module name to import <None>
      function: name of function in module to extract praser parameter from <"get_args">
      package : The 'package' argument is required when performing a relative import. It
                specifies the package to use as the anchor point from which to resolve the
                relative import to an absolute import. <None>
  
      verbose : True / False <False>
      
      
    Example:
    --------    
      from jumeg.JuMEG_ArgParser import JuMEG_ArgParser
      JAP = JuMEG_ArgParser(module="jumeg.jumeg_merge_meeg",function="get_args")
      JAP.apply()
      JAP.get_args
      
    """
    def __init__(self,**kwargs):  #module=None,function="get_args",package=None,verbose=False,extention=".py",*kargs, **kwargs):
        super(JuMEG_ArgParserBase,self).__init__()
        
        self.JFunctionParser = JuMEG_IoUtils_FunctionParser()
      #--- parser sorted  
        self._parser_args_dict= dict()
        self._opt             = None  
        self._args_as_dict    = None    
      #--- 
        self._update_kwargs(**kwargs)
        
        
   #---the arg parser   
    @property
    def parser(self): return self._parser
    @parser.setter
    def parser(self,v):  self._parser=v
   #---
    @property
    def parse_args(self): return self._parser.parse_args()
   #--- 
    @property
    def args_dict(self)  : return self._args_as_dict
    @args_dict.setter
    def args_dict(self,v): self._args_as_dict=v
   #---
    def get_args_dict(self,k):
        """ """
        return self._args_as_dict.get(k)
   #---
    def set_args_dict(self,k,v):
        """ """
        self._args_as_dict[k] = v
   #---
    @property
    def groups(self): return self.parser._action_groups
   #--- 
    def get_group(self,i):
        """ get group_action from an action by index
        Parameters:
        -----------
        i : integer
        
        Results:
        --------
        group of actions from an action
        
        Example:
        --------    
        JAP.get_action_group_action(1)
           [_StoreTrueAction(option_strings=['-b', '--set_bads'], ..),
            _StoreTrueAction(option_strings=['-v',] ..) ]
        """
        return self.parser._action_groups[i]._group_actions
  
   #--- 
    def SetVerbose(self,value=False):
        self.verbose=value    
   #--- 
    def get_group_object(self,group=None,index=None):
        """ <argparse._ArgumentGroup object """
        if group:
           if index: return group[index] #._group_actions()
           return group._group_actions  
   #---   
    def get_obj_default(self,obj):
        """ """
        return obj.default or ''
    
    def isHelpAction(self,obj):
        if str( type(obj) ).endswith('_HelpAction\'>')       : return True
    def isStoreAction(self,obj):
        if str( type(obj) ).endswith('_StoreAction\'>')      : return True
    def isStoreTrueAction(self,obj):
        if str( type(obj) ).endswith('_StoreTrueAction\'>')  : return True
    def isStoreFalseAction(self,obj):
        if str( type(obj) ).endswith('_StoreFalseAction\'>') : return True
    def isStoreTrueFalseAction(self,obj):
        if self.isStoreTrueAction(obj) : return True
        if self.isStoreFalseAction(obj): return True
  #---
    def update(self,**kwargs):
        """ update args
        add fullfile and make path from jumeg to filter
        module=None,function=None,package=None   fullfile=command.fullfile
        """
        self.import_parser_arguments_from_function(**kwargs)
  #---
    def import_parser_arguments_from_function(self,**kwargs):
        """
        import <function> from a script/module and
        get program arguments [parser.parse_args(), parser ] form this function
        the function should return < parser.parse_args() > and  < parser > obj from < argparse.ArgumentParser >
          
        Parameters:
        -----------                
         function: function name to get parser arguments from <None>
         module  : name of module to import <None>
         package: start module path <None>
            
        Results: 
        --------
         parser : parser obj
        
        Example:
        --------
         parser = self.import_argument_parser_parameter(module="jumeg.jumeg_merge_meeg",function="get_argv",package=None):
               
        Dependency:
        -----------
         importlib,sys,argparse   
         https://stackoverflow.com/questions/437589/how-do-i-unload-reload-a-python-module
        """
        self._update_kwargs(**kwargs)
        self._parser       = None 
        self._args_obj     = None
        self._args_as_dict = None

        try:
           if not os.path.isfile( self.fullfile ):
              msg = "JuMEG_ArgParserBase:import_parser_arguments_from_function : python module not exist: \n ---> " + self.fullfile
              wx.LogError(msg)
              pub.sendMessage("MAIN_FRAME.MSG.ERROR",msgtxt=msg)
              return
           self.JFunctionParser.fullfile = self.fullfile
           self.JFunctionParser.function = self.function
          #--- get args obj,parser obj from function of module 
           args=[]
           self._args_obj,self._parser = self.JFunctionParser.apply(args) 
          #--- get dict from args obj for later use key/value   
           self._args_as_dict = vars( self._args_obj )
        except Exception as e:
            # warnings.warn("Error in import ArgvParser function:\n -> module: "+ self.module+"\n -> function: "+self.function, ImportWarning)
           err_msg ="\nError in import ArgvParser function:\n   ->module: {}\n   ->function: {}\n   ->fullfile: {}\n".format(self.module,self.function,self.fullfile)
           raise type(e)(str(e) +err_msg).with_traceback(sys.exc_info()[2])

        # jb.pp(self.parser) 
        return self.parser       

class JuMEG_ArgParser(JuMEG_ArgParserBase):
    """
    JuMEG_ArgParser interface <argparse> to GUI
    import <function> from a script/module and
    get program arguments [parser.parse_args(), parser ] form this function
    the function should return <parser.parse_args()> and  < parser > obj from < argparse.ArgumentParser >
     
    Parameters:
    -----------
     module  : module name to import <None>
     function: name of function in module to extract praser parameter from <"get_args">
     package : The 'package' argument is required when performing a relative import. It
                specifies the package to use as the anchor point from which to resolve the
                relative import to an absolute import. <None>
     verbose : True / False <False>
      
    Example:
    --------    
      from jumeg.gu.jumeg_gui_wx_argparser import JuMEG_ArgParser
      JAP = JuMEG_ArgParser(module="jumeg.jumeg_merge_meeg",function="get_args")
      
      or use
      JAP.module   = "jumeg.jumeg_merge_meeg"
      JAP.function = "get_args"
      JAP.update()
      
      JAP.get_args

    Example Argparser function:
    ---------------------------
     special behavior for MEG file, EEG file or Text file arguments:
     in <parser.add_argument> use <metavar> to code GUI bevavior to display file, file extention, list file, start path (stage)
     split metavar with ('_') into  <Group Title>,<MagicKey>, rest
    
    
     Translation into GUI:
      <help>    ToolTip shows help text
      
      <default> is the deafault to displayed 
      
      <metavar>="MEG_FILENAME
       parser.add_argument("-fmeg","--meg_file_name",help="meg fif file + relative path to stage", metavar="MEG_FILENAME")
          
       In a panel with Title <MEG> a File Dialog Button with label <File> and textcontrol are display
       click on <File> will popup a file dialog, selected file will be shown in textcontrol or default filename
       filename is relative to start path <meg_stage>
       
      <metavar>="MEG_STAGE
       parser.add_argument("-smeg","--meg_stage", help=info_meg_stage,metavar="MEG_STAGE",default="/data/exp/M100/mne")
     
       In a panel with Title <MEG> a Directory Dialog Button with label <Stage> and textcontrol are display
       click on <Stage> will popup a directory dialog, selected directory will be shown in textcontrol or default <stage>
      
      <metavar>="MEG_FILEEXTENTION"  
       Hiden information will be passed to <MEG> file dialog as file extention
       parser.add_argument("-fmeg_ext", "--meg_file_extention",help="meg fif file extention", default="FIF files (*.fif)|*.fif", metavar="MEG_FILEEXTENTION")

      <metavar>=None
       parser.add_argument("-bads", "--bads_list", help="apply bad channels to mark as bad works only with <--set_bads> flag",default=("MEG 007,MEG 142,MEG 156,RFM 011") ) 
       arguments are treated as strings displayed in a textcontrol
       e.g.: will show label <bads> and a text control to edit 
            
       
       <choices> are defined 
       a ComboBox will be displayed instead of a textcontrol and shows list of choices
      
       <action>="store_true"
       check box will be displayed
    
     Example Function:
     -----------------
     def get_args(argv):
        
         import argparse
         parser = argparse.ArgumentParser("Example")
     
       #---MEG
         parser.add_argument("-fmeg","--meg_file_name",help="meg fif file + relative path to stage", metavar="MEG_FILENAME")
         parser.add_argument("-smeg","--meg_stage", help=info_meg_stage,metavar="MEG_STAGE",default="/data/exp/M100/mne")
         parser.add_argument("-fmeg_ext", "--meg_file_extention",help="meg fif file extention", default="FIF files (*.fif)|*.fif", metavar="MEG_FILEEXTENTION")
          
       #---textfile  
         parser.add_argument("-flist","--list_file_name",help="text file with list of files to process in batch mode",metavar="LIST_FILENAME")
         parser.add_argument("-flist_ext", "--list_file_extention",help="list fif file extention", default="list file (*.txt)|*.txt", metavar="LIST_FILEEXTENTION")
         parser.add_argument("-plist","--list_path", help=info_flist,default=os.getcwd(),metavar="LIST_PATH")
        
       #-- bads input as string
         parser.add_argument("-bads", "--bads_list", help="apply bad channels to mark as bad works only with <--set_bads> flag",default=("MEG 007,MEG 142,MEG 156,RFM 011") ) 
         
         parser.add_argument("-test", "--test", help="test choices",choices=["A","B","C"],default="B" ) 
       
       #--- parameter
         parser.add_argument("-sc",   "--startcode",type=int,help="start code marker to sync meeg and eeg data",default=128)
      
       # ---flags:
        parser.add_argument("-b", "--set_bads",action="store_true", help="apply default bad channels to mark as bad") 
        
        return parser.parse_args(), parser
        
    opt, parser = get_args(argv) 
    
    argparser:
    ---------
     https://docs.python.org/2/howto/argparse.html#the-basics
     
    """
    def __init__(self,pubsub=True,*kargs,**kwargs):
        super(JuMEG_ArgParser,self).__init__(**kwargs)
      
        self.default_io_key_list  = ["STAGE","PATH","FILENAME"]
        self.default_bad_key_list = ["FILEEXTENTION"]
        
        self._param         = dict()
        self._param_file_io = dict()
       
      #--- pubsub  
        self.use_pubsub = pubsub
        self.pub_message_call_combobox     = "CLICK_ON_COMBO_BOX"
        self.pub_message_call_checkbox     = "CLICK_ON_CHECK_BOX"
        self.pub_message_call_fileiobutton = "CLICK_ON_FILE_IO_BUTTON"
       
        if self.use_pubsub:
           pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
   #--- 
    def set_cmd_parameter(self,key,opt,v):
        """ set cmd parameter dict
        
        Parameters:
        -----------    
        key, option-key, value
                
        """
        if not self._param.get(key)     : self._param[key]      = dict()
        if not self._param[key].get(opt): self._param[key][opt] = dict()
        self._param[key][opt] = v        
   #---     
    def get_cmd_parameter(self,key,option=None):
        """
        get cmd parameter dict
        
        Parameters:
        -----------    
        key
        option: <None>
        
        Results:
        --------
        value or cmd parameter dict
        
        Example:
        --------    
        { 'bads_list': {   '-bads': 'MEG 007,MEG 142,MEG 156,RFM 011'},
          'meg_file_extention': {   '-fmeg_ext': 'FIF files (*.fif)|*.fif'},
          'meg_file_name': {   '-fmeg': None},
          'meg_stage': {   '-smeg': '/home/fboers/MEGBoers/data/exp/MEG94T/mne'},
          'meg_stim_channel': {   '-megst': 'STI 014'},
          'verbose': {   '-v': False}}   
        """
        
        if self._param.get(key):
           if option : return self._param[key].get(option)
           if key    : return self._param.get(key)
        return self._param
   #--- 
    def get_metavar_array(self,obj):
        if not obj.metavar  : return
        meta = obj.metavar.split('_') # MEG_STAGE
        if (len(meta) < 2)  : return
        return meta 
   #---
    def is_metavar_in_bad_list(self,obj):
        """ """ 
        meta = self.get_metavar_array(obj)
        if meta:
           return ( meta[1] in ",".join(self.default_bad_key_list) )
   #---  
    def get_metavar_as_list(self,obj):
        """ """
        meta = self.get_metavar_array(obj)
        if not meta : return
        if not meta[1] in self.default_io_key_list: return
        return meta
    
    def get_extention_obj(self,name):
        """
        finds the obj for file extention 
        use for FileDialog
        
        Parameters:
        -----------
        obj: should has something like metavar="MEG_FILENAME"
        
        Results:
        ---------
        file extention 
        
        Example:
        --------    
        "XYZ files (*.xyz)|*.xyz",
        
        """
        key = name.split('_')[0].lower() + "_file_extention" # meg_file_extention
        return self.get_args_dict(key)

   #---
    def set_cmd_parameter_file_io(self,obj):
        """
        check if is file io parameter
        needs obj with metavar option and has to be in io-key-list
        
        set cmd file io parameter
        dict of lists of dicts
        
        Parameters:
        -----------
        action obj with metavar-option
        
        Results:
        --------
        True or False
        """
        meta = self.get_metavar_as_list(obj)  
        
        if not meta: return
        
        if not self._param_file_io.get( meta[0] ):
           self._param_file_io[ meta[0] ] = []
           
        self._param_file_io[ meta[0] ].append( { meta[1]:obj } )
        
        return True
       
   #--- 
    def get_cmd_parameter_file_io(self,key=None,idx=None,option=None):
        """
        get file io cmd parameter
        dict of lists of dicts
        
        Parameters:
        -----------
        key    : key in main-dict <None>
        idx    : index in list    <None>
        option : key of dict to store action obj <None>
        
        """
        
        if option: 
           return self._param_file_io[key][idx][option] 
       #--- return dict <label> :_StoreAction obj
        if jb.isNumber(idx):
           return self._param_file_io[key][idx] 
        if key:
           return self._param_file_io[key]
        
        return self._param_file_io  
   #---      
    def obj_to_flag_list(self,obj):
        """
        append list of CheckButtons to display later
        [( control type,name,label,value,help.callback) ...]
        
        Parameter:
        ----------
        action object
        
        """
        return ["CK",obj.dest,obj.dest,obj.default,obj.help,self.ClickOnCheckBox]
   
   #--- 
    def obj_to_control_list(self,obj):
        """
        append list of wxControls  to display later
        ComboBox for choices or TxtCtrl
        
        ComboBox: ( control type,name,value,choices,help,callback) 
                  ("COMBO","COLOR","red",['red','green'],'select a color',ClickOnComboBox)
        
        TxtCtrl : ( control type,name,label,help,callback) 
     
        Parameter:
        ----------
        action object
        
        """
        if obj.default:
           v = str( obj.default )
        else: v = ''
           
        if obj.choices:
           if v == '': v = obj.choices[0] 
           return ["COMBO",str(obj.dest).upper(),v,obj.choices,obj.help,self.ClickOnComboBox]
        else:   
           return ["TXT",str( obj.dest ).upper(),v,obj.help,None]
       
   #---
    def groups_to_ctrl_lists(self):
        """
        groups_to_ctrl_lists
        """
        control_list = []
        flag_list    = []
        
        for group in self.groups:
            for obj in self.get_group_object(group):
                
                if self.isHelpAction(obj) : continue
            
                self.set_cmd_parameter(obj.dest,obj.option_strings[0],obj.default) 
             
                if self.isStoreAction(obj): 
               #--- chek for filename io e.g  stage,filename  File-,Dirdialog
                   if not self.set_cmd_parameter_file_io(obj):
                      if self.is_metavar_in_bad_list(obj): continue
                      control_list.append( self.obj_to_control_list(obj))
                      continue
               #--- flag list for CheckButtons
                if self.isStoreTrueFalseAction(obj):
                   flag_list.append( self.obj_to_flag_list(obj) )
       
        return control_list,flag_list
    
   #---
    def groups_to_io_ctrl_list(self,k):
        """ 
        groups_to_io_ctrl_list
        """
        io_list = []
        for idx in range(len(self.get_cmd_parameter_file_io(key=k))) : # list => STAGE FILENAME from MEG_STAGE,MEG_FILENAME
            obj_dict = self.get_cmd_parameter_file_io(key=k,idx=idx) # get dict {key: obj} e.g. {FILENAME:_StoreAction( ... )}
            for option_name in obj_dict: # should be only one {key: obj}
                obj = self.get_cmd_parameter_file_io(key=k,idx=idx,option=option_name) #  get the obj
               #--- Button  : ( control type,name,label,help,callback)
                io_list.append(["BT",str(obj.dest).upper(),option_name,obj.help,self.ClickOnFileIOButton ])
               #--- TxtCtrl : ( control type,name,label,help,callback) 
                io_list.append(["TXT",str(obj.dest).upper(),self.get_obj_default(obj),obj.help,None])
    
        return io_list       
    
   #---
    def args_dict_to_cmd(self,verbose=False):
        """ 
        Results:
        --------
        cmd with parameter to pass to execute in batch mode
        
        """
        cmd=dict()
        if not self.module:
            cmd["name"] = os.path.basename(self.fullfile)
        else:
            cmd["name"] = self.module.split('.')[-1] + self.extention
        cmd["io"]     = []
        cmd["txt"]    = []
        cmd["flags"]  = []
        jb.pp(self.args_dict.items())

        for k,v in self.args_dict.items():
            if k.upper().replace("_","").endswith(tuple( self.default_bad_key_list )): continue
           #--- ck file io 
            if k.upper().endswith(tuple(self.default_io_key_list)):  # FILENAME,STAGE,PATH
              #--- ck file io
               if not v     : continue
               if v.strip() : cmd["io"].append("--"+k+"="+v)
               continue              
           #---ck for flags 
            if isinstance(v,bool): # only store True 
               if v: 
                  cmd["flags"].append("--"+k)
                  continue
           #--- txt fields 
            elif bool(v.strip()) : 
                 if " " in v:  v= '"'+v+'"' # e.g. for stim channel "STI 014"
                 cmd["txt"].append("--"+k+"="+v)    
            
        if self.verbose or verbose:
           jb.line()
           print(" --> JuMEG ArgParser CMD:")
           print(" --> Module   : {}".format(self.module))
           print(" --> Function : {}".format(self.function))
           print(" --> IO       : {}".format(cmd["io"]))
           print(" --> Parameter: {}".format(cmd["txt"]))
           print(" --> Flags    : {}".format(cmd["flags"]))
           cmdstr = cmd["name"] +" "+" ".join(cmd["io"]) +" "+" ".join(cmd["txt"]) +" "+" ".join(cmd["flags"])
           print("\n  ->CMD: ")
           print( cmdstr )
           jb.line()
        return cmd    
   #---
    def get_command(self,verbose=False,ShowFileIO=True,ShowParameter=True):  
        """
        Parameter
        ---------
        ShowFileIO    : <True>
        ShowParameter : <True>
        verbose       : <False>
        
        Results
        --------
        command as string
        with parameter to pass to execute in batch mode
        """                  
        cmd    = self.args_dict_to_cmd(verbose=verbose)
        cmdstr = cmd["name"]
        if ShowFileIO   : cmdstr += " "+" ".join(cmd["io"]) 
        if ShowParameter: cmdstr += " "+" ".join(cmd["txt"])+" "+" ".join(cmd["flags"])
        return cmdstr
  #---
    def get_fullfile_command(self,verbose=False,ShowFileIO=True,ShowParameter=True):  
        """
        Parameter
        ---------
        ShowFileIO    : <True>
        ShowParameter : <True>
        verbose       : <False>
        
        Results
        --------
        fullfile path command and aparameter string
        with parameter to pass to execute in batch mode
        """                  
        cmd    = self.args_dict_to_cmd(verbose=verbose)
        cmdstr = self.fullfile
        if ShowFileIO   : cmdstr += " "+" ".join(cmd["io"]) 
        if ShowParameter: cmdstr += " "+" ".join(cmd["txt"])+" "+" ".join(cmd["flags"])
        return cmdstr   
   #--- 
    def ClickOnFileIOButton(self,evt):
        """ """
        if self.use_pubsub:
           pub.sendMessage(self.pub_message_call_fileiobutton,event=evt)  
            
        else: evt.Skip()
   #--- 
    def ClickOnComboBox(self,evt):
        """ """ 
        if self.use_pubsub:
           pub.sendMessage(self.pub_message_call_combobox,event=evt)      
        else: evt.Skip()
   #---      
    def ClickOnCheckBox(self,evt):
        """ """
        if self.use_pubsub:
           pub.sendMessage(self.pub_message_call_checkbox,event=evt)      
        else: evt.Skip()

     
class JuMEG_wxArgvParserBase(wx.Panel): ##scrolled.ScrolledPanel):
    """
    JuMEG_wxArgvParserBase  base CLS functions to ovewrite
    
    Paremeters:
    -----------    
    pubsub       : use wx.pupsub msg systen <False>
                     example: pub.sendMessage('EXPERIMENT_TEMPLATE',stage=stage,experiment=experiment,TMP=template_data)
                     or button event from  <ExpTemplateApply> button for apply/update   
    verbose      : <False>
    bg           : backgroundcolor <grey90>
       
    """
    def __init__(self,*kargs,**kwargs):
        super().__init__(*kargs,id=wx.ID_ANY,style=wx.SUNKEN_BORDER)
        self.use_pubsub = None
        self.debug      = False
        self.verbose    = False
        self._param     = {} 
        #self._init()

    def _get_param(self,k1,k2):
        return self._param[k1][k2]
    def _set_param(self,k1,k2,v):
        self._param[k1][k2]=v
   
    def _init(self,**kwargs):
        self.use_pubsub = kwargs.get("pubsub",True)
        self.debug      = kwargs.get("debug",False)
        self.verbose    = kwargs.get("verbose",False)
        
        if self.use_pubsub:
           pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
           self._init_pusub_calls()
      
        self._wx_init(**kwargs)
        self.update(**kwargs)
        self._ApplyLayout()
     
    def SetVerbose(self,value=False):
        self.verbose=value
                  
    def _init_pusub_calls(self):
        pass

    def _wx_init(self,**kwargs):
        pass 
        
    def update(self,**kwargs):
        pass
    
    def _ApplyLayout(self):
        """ ovewrite """
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)
   
    def clear_parameter(self):
        pass
     
    def clear_children(self,wxctrl):
        for child in wxctrl.GetChildren():
            child.Destroy()
        self.Layout()
        self.Fit()  
        
    def clear(self,wxctrl=None):
        """ clear delete wx childeren """
        self.clear_parameter()
       #--- clear wx stuff
        self.clear_children(self)

        
class JuMEG_wxArgvParserIO(ScrolledPanel):
    """
    JuMEG_GUI_wxArgvParser, a wxGUI to show arguments from a python-script,
    parsed by <argparse> module. In the python-scriptthere has to be a <get_argv()> to
    provide the parser arguments
      
    https://docs.python.org/2/howto/argparse.html#
      
    Parameters:
    ----------
     module  : module / python-script to show parser arguments
     function: function name wthin the module <get_argv>
     pubsub  : use pubsub <False>
     bg      : background color <blue>
     ShowCloseButton: False

    Example:
    --------    
     from jumeg.gui.jumeg_gui_wx_argparser import JuMEG_GUI_ArgvParserFrame
       
     module = "jumeg.jumeg_merge_meeg"
     frame  = JuMEG_GUI_ArgvParserFrame(None,-1,'JuMEG MEEG MERGER ARGY Parser FZJ-INM4',module=module )
     frame.Show()
     app.MainLoop()
       
     !! inside the python-script there is the <get_avg> function to parse arguments to the script
 
     def get_args():
         parser = argparse.ArgumentParser("INFO")
          
    
       #---input files
         parser.add_argument("-fmeg", "--meg_fname",help="meg fif file + full path", metavar="MEG_FILENAME")
         parser.add_argument("-smeg","--stage_meg", help=info_meg_stage,metavar="MEG_STAGE")
       #---textfile  
         parser.add_argument("-flist","--fname_list",help="text file with fif files",metavar="TEXTLIST_FILENAME")
         parser.add_argument("-plist","--path_list", help=info_flist,default=os.getcwd(),metavar="TEXTLIST_PATH")
    
       #--- bads
         parser.add_argument("-bads", "--bads_list", help="apply bad channels to mark as bad works only with <--set_bads> flag",default=("MEG 007,MEG 142,MEG 156,RFM 011") ) 
   
       #--- parameter
         parser.add_argument("-sc",   "--startcode",type=int,help="start code marker to sync meeg and eeg data",default=128)
       
       #---flags:
         parser.add_argument("-b", "--set_bads",action="store_true", help="apply default bad channels to mark as bad") 
         parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
         return parser.parse_args(), parser
          
    """
    def __init__(self,parent,**kwargs):
        super().__init__(parent)
        self.verbose       = False
        self.ShowParameter = False
        self.ShowFileIO    = False

       #--- arg parser   
        self.parser = JuMEG_ArgParser(**kwargs)
        
       #--- use pubsub to close frame
        if self.parser.use_pubsub:
           pub.subscribe(self._pubsClickOnComboBox,    self.parser.pub_message_call_combobox)
           pub.subscribe(self._pubsClickOnCheckBox,    self.parser.pub_message_call_checkbox)
           pub.subscribe(self._pubsClickOnFileIOButton,self.parser.pub_message_call_fileiobutton)
           pub.subscribe(self.SetVerbose,"MAIN_FRAME.VERBOSE")
           
       #--- WX stuff 
        self.SetBackgroundColour( kwargs.get("bg","grey20") )
       #--- wx panels   
        self._pnl_parameter = None
        self._pnl_file_io   = None
          
       #---  wx control list  
        self._wxctrl_list_of_controls     = []
        self._wxctrl_list_of_flags        = []
        self._wxctrl_list_of_file_io_keys = []
        self._wxctrl_list_of_buttons      = []
   #---
    def SetVerbose(self,value=None):
        self.verbose=value
        if self.parser:
           self.parser.verbose = value 
   #--- 
    def _update_kwargs(self,**kwargs):
        """ update kwargs"""
        self.verbose        = kwargs.get("verbose",False)
        self.ShowParameter  = kwargs.get("ShowParameter",self.ShowParameter)
        self.ShowFileIO     = kwargs.get("ShowFileIO",self.ShowFileIO)
   #---   
    def update(self,**kwargs):
        """ update """
        self._update_kwargs(**kwargs)
        
       #---  update coltrol lists with argparser obj  
        self.parser.update(**kwargs)
        self._wxctrl_list_of_controls,self._wxctrl_list_of_flags = self.parser.groups_to_ctrl_lists()
       
        if self.ShowFileIO   : self._update_file_io()
        if self.ShowParameter: self._update_parameter()
        
        self._ApplyLayout()
   #---       
    def _update_parameter(self):
        """ update panel parameter """ 
        self._pnl_parameter = wx.Panel(self, -1,style=wx.SUNKEN_BORDER)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
       #--- get wx.GridSizers for Controls and CheckBoxes  
        pnl_controls = JuMEG_wxControls(   self._pnl_parameter,label="Parameter",control_list=self._wxctrl_list_of_controls,AddGrowableCol=2,set_ctrl_prefix=False)
        pnl_flags    = JuMEG_wxControlGrid(self._pnl_parameter,label="Flags",    control_list=self._wxctrl_list_of_flags,cols=1,set_ctrl_prefix=False)
        
        hbox.Add(pnl_controls,1,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,4)
        hbox.Add(pnl_flags,   0,wx.ALIGN_RIGHT|wx.ALL,4)
        
        self._pnl_parameter.SetSizer(hbox)           
        self._pnl_parameter.SetAutoLayout(1)
   #---  
    def _update_file_io(self):
        """ update file io panel """
        self._pnl_file_io = wx.Panel(self,style=wx.SUNKEN_BORDER) 
        vbox = wx.BoxSizer(wx.VERTICAL)
        ds   = 1
        
        for k in self.parser.get_cmd_parameter_file_io().keys(): # list of dicts => MEG EEG
          #---  get list of io-controls definition
            io_list = self.parser.groups_to_io_ctrl_list(k)
         #--- io controls
            pnl_io_ctrl = JuMEG_wxControlIoDLGButtons(self._pnl_file_io,label=k,control_list=io_list,AddGrowableCol=1)
            vbox.Add(pnl_io_ctrl,0,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,ds)
            vbox.Add((0,0),1,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,ds)
     
        self._pnl_file_io.SetSizer(vbox)           
        self._pnl_file_io.SetAutoLayout(1)
   #---      
    def _get_button_name(self,bt):
        """ 
        extract button name 
        Parameters:
        -----------
        wx ctrl-obj or string
        
        Results:
        --------
        button name, IO type
        
        Example:
        --------
        BT_meg_filename => meg_filename,MEG
        
        """
        if isinstance(bt,str):  # button name : meg_filename
           bt_name = bt.replace("BT.","")
        else:
           bt_name = bt.GetName().replace("BT.","") # bt wx ctrl obj
        return bt_name,bt_name.split("_")[0].upper()    
   #---    
    def _get_io_txtctrl(self,s):
        """
        find <io_type> txtctrl obj  [XYZ, MEG,EEG,LIST]
        
        Parameter:
        ----------            
        string
        
        Result:
        -------
        wx textctrl obj for stage/path
        wx textctrl obj for filename
        
        Example:
        --------
        stage_obj,filename_obj = self._get_io_txtctrl("XYZ") 
                
        """
        stage_obj = None
        for p in ["stage","path"]:
            io_type = s.lower() +"_"+ p
            if io_type in self.parser.args_dict.keys():
               stage_name  = "TXT."+s.upper() +"_"+ p.upper()
               stage_obj   = self.FindWindowByName( stage_name )
               file_name   = "TXT."+s.upper() + "_FILENAME"
               file_obj    = self.FindWindowByName(file_name)
               continue
        return stage_obj,file_obj
   #---       
    def _get_button_txtctrl(self,obj):
        """ finds the textctr related to the button event 
        Parameters:
        -----------
        wx control button
        
        Results:
        ---------
        wx textctrl obj
        
        """
        return self.FindWindowByName( obj.GetName().replace("BT.","") )
   #---      
    def ClickOnFileIOButton(self,evt):
        """
        ClickOnFileIOButton
         -> select stage --> select file
        
        """
       #--- get caller button and find related txtctrl
        bt_obj            = evt.GetEventObject() 
        bt_label          = bt_obj.GetLabel()
        #wx.LogMessage("936 bt: {} {}".format(bt_obj.GetLabel(), bt_obj.GetName() ))
        bt_name,io_type   = self._get_button_name(bt_obj)
        stage_obj,filename_obj = self._get_io_txtctrl(io_type)

        #wx.LogMessage("936 stage obj: {} {}".format(stage_obj, stage_obj.GetName() ))
        #wx.LogMessage("936 file obj: {} {}".format(filename_obj, filename_obj.GetName()))

       #--- Stage  only DIR
        if bt_label.title().startswith("Stage") or bt_label.title().startswith("Path"):
           dlg = wx.DirDialog(self,io_type +" : Choose Stage directory","",wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
           dlg.SetPath( stage_obj.GetValue() )
           if (dlg.ShowModal() == wx.ID_OK):
              stage_obj.SetValue( os.path.normpath( dlg.GetPath() ) )  # if add "/"
              filename_obj.SetValue("") # clear filename field 
           dlg.Destroy()
           return
       
       #--- File File DLG for e.g:  meg,eeg
        if bt_label.title().startswith("File"):
           dlg = wx.FileDialog(self,io_type+" : Select file", wildcard="all files (*.*)|*.*",style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) 
           dlg.SetWildcard( self.parser.get_extention_obj(bt_name) )
          #--- get txt crtl for stage or path 
           if stage_obj:
              dlg.SetDirectory( stage_obj.GetValue() ) 
               
           if dlg.ShowModal() == wx.ID_CANCEL:     
              return 
           
           if not dlg.GetPath(): return
          #--- ck stage  for relative path to filename or set stage     
           if os.access(dlg.GetPath(),os.R_OK): # file name + path
              if dlg.GetPath().startswith(stage_obj.GetValue()): # common stage path
                 f_relative = dlg.GetPath().rsplit( os.path.normpath( stage_obj.GetValue() ) +"/" )[-1] 
                 filename_obj.SetValue( f_relative )
              else:
                 stage_obj.SetValue( os.path.dirname( dlg.GetPath() ) )  
                 filename_obj.SetValue( os.path.basename( dlg.GetPath() ) ) 
           else:
              wx.LogError("No read permissions: '%s'." ) % dlg.GetPath()
           dlg.Destroy()
           return
           
   #-- call from pubsub 
    def _pubsClickOnButton(self,event=None):
        self.ClickOnButton(event)
    def _pubsClickOnComboBox(self,event=None):
        self.ClickOnComboBox(event)  
    def _pubsClickOnCheckBox(self,event=None):
        self.ClickOnCheckBox(event)
    def _pubsClickOnFileIOButton(self,event=None):
        self.ClickOnFileIOButton(event)  
   #---  
    def update_parameter(self):
        """
        xyz_filename => metavar XYZ_FILENAME
        xyz_stage    => metavar XYZ_STAGE
        
        """
        for k in self.parser.args_dict.keys():
            obj = self.FindWindowByName(k)
            if obj:  # no file io ctrl
               self.parser.set_args_dict(k,obj.GetValue())
          
        return self.parser.args_dict_to_cmd()        
     
   #--- 
    def ClickOnButton(self,evt):
        """ """
        obj = evt.GetEventObject()
        
        if obj.GetName().startswith("BT.APPLY"):
           self.update_parameter()
           
        if obj.GetName().startswith("BT.CLOSE"):
           if self.parser.use_pubsub:
              pub.sendMessage('MAIN_FRAME.CLICK_ON_CLOSE',evt=evt)
           elif callable(self.GetParent().ClickOnClose):
                self.GetParent().ClickOnClose(evt)
        else:
           evt.Skip()
             
             
    def ClickOnComboBox(self,evt):
         obj = evt.GetEventObject()
         self.parser.args_dict[obj.Name] = obj.GetValue()

    def ClickOnCheckBox(self,evt):
        pass
      
    def _ApplyLayout(self):
        """ set panels like:
              
              IO
          ----------
          TXT | CKB
          ----------
        """
        ds1=2
        LEL= wx.ALIGN_LEFT|wx.EXPAND|wx.ALL
        #REL = wx.ALIGN_RIGHT|wx.EXPAND|wx.ALL
        
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
       #--- 
        if self.ShowFileIO   : self.Sizer.Add(self._pnl_file_io,0,LEL,ds1) 
        if self.ShowParameter: self.Sizer.Add(self._pnl_parameter,0,LEL,ds1)
        #if self.show_buttons  : self.Sizer.Add(self._pnl_buttons,0,LEL,ds1) 
        
        self.SetSizer(self.Sizer)
        self.Sizer.Fit(self)
        self.SetAutoLayout(1)
        self.SetupScrolling()        
   #--- 
    def _clear_parameter(self)  :
        self._param         = dict()
        self._param_file_io = dict()
       #---  wx control list  
        self._wxctrl_list_of_controls     = []
        self._wxctrl_list_of_flags        = []
        self._wxctrl_list_of_file_io_keys = []
        self._wxctrl_list_of_buttons      = []
   #--- 
    def clear(self):
        """ clear delete wx childeren """
        
        self._clear_parameter()
          
       #--- clear wx stuff
        for child in self.GetChildren():
            child.Destroy()
       #--- 
        self._pnl_file_io  = None       
        self._pnl_parameter= None
        self._pnl_buttons  = None
       #--- 
        self.Layout()
        self.Fit()              
   #---  
    def _update_parser_dict(self):
        """
        xyz_filename => metavar XYZ_FILENAME
        xyz_stage    => metavar XYZ_STAGE
        
        """
        for k in self.parser.args_dict.keys():
            obj = self.FindWindowByName(k.upper())
            if obj:  # no file io ctrl
               self.parser.set_args_dict(k,obj.GetValue())
            elif  k.upper().split("_")[-1] in set( self.parser.default_io_key_list ):
                  obj = self.FindWindowByName("TXT."+k.upper())
                  self.parser.set_args_dict(k,obj.GetValue())
   #---  
    def get_command(self,**kwargs):
        self._update_parser_dict()    
        return self.parser.get_command(**kwargs)   
   #---  
    def get_fullfile_command(self,**kwargs):
        self._update_parser_dict()    
        return self.parser.get_fullfile_command(**kwargs)   
   #---
    def get_parameter(self,**kwargs):
        self._update_parser_dict()
        cmd = self.parser.args_dict_to_cmd()
        return " ".join(cmd["txt"])+" "+" ".join(cmd["flags"])


class JuMEG_wxArgvParserCMD(JuMEG_wxArgvParserBase):
    """
     Paremeters:
     -----------
      pubsub   : use wx.pupsub msg systen <False>
                 example: pub.sendMessage('EXPERIMENT_TEMPLATE',stage=stage,experiment=experiment,TMP=template_data)
                 or button event from  <ExpTemplateApply> button for apply/update
      verbose  : <False>
      bg       : backgroundcolor <grey90>
    """

    def __init__(self, *kargs, **kwargs):
        super(JuMEG_wxArgvParserCMD, self).__init__(*kargs)
        self.JModule = JuMEG_IoUtils_JuMEGModule()
        self.JCMD    = JuMEG_IoUtils_FunctionParserBase(**kwargs)
        self._init(**kwargs)

    def _wx_init(self, **kwargs):
        # ---
        self.SetBackgroundColour(kwargs.get("bg", "grey60"))

        ctrl_list = []
        ctrl_list.append(("BT", "UPDATE", "UPDATE", "update command parameter", self.ClickOnCTRL))
        ctrl_list.append(("COMBO", "COMMAND", "COMMAND", [], "select a command / module", self.ClickOnCTRL))
        self.pnl_ctrls = JuMEG_wxControlGrid(self, label="Command", control_list=ctrl_list, cols=len(ctrl_list),AddGrowableCol=[1])

  #--- CMD ComboBox
        pub.subscribe(self._refresh,"COMMAND_REFRESH")

    def _update_kwargs(self, **kwargs):
        self.use_pubsub = kwargs.get("pubsub", True)
        self.verbose = kwargs.get("verbose", False)

    def update(self, **kwargs):
        self._update_kwargs(**kwargs)
        self._refresh()

    def _refresh(self,**kwargs):
        self.JCMD.update(**kwargs)
        self.JModule.FindModules(**kwargs)
        self.RefreshCommandComboBox()

    def RefreshCommandComboBox(self):
        """
        refresh command list in ComboBox
        get exe py filenames from PYTHONPATH jumeg
        """
        obj = self.FindWindowByName("COMBO.COMMAND")
        if obj:
           self.pnl_ctrls.UpdateComBox(obj,self.JModule.ModuleNames())
           self.UpdateCommandComboBox()

    def UpdateCommandComboBox(self):
        """
         update command combobox
        """
        # --- get exe py filenames from PYTHONPATH jumeg
        obj = self.FindWindowByName("COMBO.COMMAND")
        idx = obj.GetSelection()

        self.JCMD.name = self.JModule.ModuleNames(idx)
        self.JCMD.fullfile = self.JModule.ModuleFileName(idx)
        self.JCMD.prefix = self.JModule.stage_prefix
        self.JCMD.function = self.JModule.function

        if self.verbose:  self.JCMD.info()

        if self.use_pubsub:
            pub.sendMessage('COMMAND_UPDATE', command=self.JCMD.command)

    def ClickOnCTRL(self, evt):
        # --- click on CommandComboBox
        obj = evt.GetEventObject()

        if obj.GetName().startswith("COMBO.COMMAND"):
            self.module = self.FindWindowByName("COMBO.COMMAND").GetValue()
            self.UpdateCommandComboBox()
        # --- click on Command Update Button
        elif obj.GetName().startswith("BT.UPDATE"):
            self._refresh()
        else:
            evt.Skip()

    def _ApplyLayout(self):
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.pnl_ctrls, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, 3)
        self.SetSizer(self.Sizer)
        self.SetAutoLayout(1)

class JuMEG_GUI_wxArgvParser(JuMEG_wxMainPanel):
    """
    JuMEG_GUI_wxArgvParser, a wxGUI CLS to show arguments from a python-script,e.g. executable command (CMD),
    parsed by <argparse> module.

    Parameters:
    ----------
    ShowAll
    ShowCommand
    ShowFileIO
    ShowParameters
    ShowButtons
    ShowPBSHosts

    Results:
    --------
    wx.Panel

    """
    def __init__(self,parent,**kwargs):
        super().__init__(parent,name="JUMEG_ARGPARSER_PANEL")
        self._param = { "show"   :{"All":False,"Command":False,"FileIO":False,"Parameter":False,"Buttons":True,"PBSHosts":False}}


        self.SubProcess = JuMEG_IoUtils_SubProcess() # init and use via pubsub
        self.fullfile   = None
        self._init(**kwargs)

        #self.update(**kwargs)
        #self._ApplyLayout()
     
    def _get_param(self,k1,k2):
        return self._param[k1][k2]
    def _set_param(self,k1,k2,v):
        self._param[k1][k2]=v
      
    @property        
    def ShowCommand(self):   return self._get_param("show","Command")
    @property        
    def ShowFileIO(self):    return self._get_param("show","FileIO")
    @property        
    def ShowParameter(self): return self._get_param("show","Parameter")
    @property
    def ShowButtons(self):return self._get_param("show","Buttons")
    @property
    def ShowPBSHosts(self):  return self._get_param("show","PBSHosts")
    @property
    def ArgvParser(self):
        if self._pnl_argparser:
           return  self._pnl_argparser.parser

    @property
    def use_pubsub(self):   return self._use_pubsub
    @use_pubsub.setter
    def use_pubsub(self,v): self._use_pubsub = v

    def GetParameter(self):
        return self._pnl_argparser.get_parameter()

    def init_status_of_ctrls(self,**kwargs):
        """
        select panel to show 
        name,value
        all: if no <None> select all
        """
        if kwargs.get("ShowAll",False):
           for k in self._param["show"].keys():
               self._param["show"][k]=True
        else:
           for k in self._param["show"].keys():
               self._param["show"][k] = kwargs.get("Show"+k,False)

    def update_from_kwargs( self, **kwargs ):
        self.init_status_of_ctrls(**kwargs)
        self._use_pubsub  = kwargs.get("use_pubsub", getattr(self.GetParent(), "use_pubsub", False))
        self.module_stage = kwargs.get("stage", os.environ['JUMEG_PATH'])  # os.environ['PWD']
        self.module       = kwargs.get("module")
        self.function     = kwargs.get("function", "get_args")
        self.fullfile     = kwargs.get("fullfile", self.fullfile)
        self.SetBackgroundColour(kwargs.get("bg", "grey88"))

    def update(self, **kwargs):
        self.update_from_kwargs(**kwargs)
        self.init_status_of_ctrls(**kwargs)

       #---
        ds=1
        LEA = wx.ALIGN_LEFT | wx.EXPAND | wx.ALL

        self.SplitterAB.Unsplit() # no PanelB
       # -- update wx CTRLs
        self.PanelA.SetTitle(v="Parameter / Flags")

       #--- TOP
        if self.ShowCommand:
           self.CommandCtrl = JuMEG_wxArgvParserCMD(self.TopPanel, **kwargs)
           self.TopPanel.GetSizer().Add(self.CommandCtrl,3,LEA,ds)
        else:
           command = { "function": self.function, "import_name": self.module, "fullfile": self.fullfile }
           self.update_wx_argparser(command=command)
        if self.ShowPBSHosts:
           self.HostCtrl  = JuMEG_wxPBSHosts(self.TopPanel, prefix=self.GetName())
           self.TopPanel.GetSizer().Add(self.HostCtrl,1, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL,ds)

        self.Bind(wx.EVT_BUTTON,self.ClickOnButton)

        if self.use_pubsub:
           self.init_pubsub()
           pub.subscribe(self.update_wx_argparser,'COMMAND_UPDATE')

    def update_wx_argparser(self,command=None):
       #--- update parser 
        for child in self.PanelA.Panel.GetChildren():
            child.Destroy()

        if ( self.ShowFileIO or self.ShowParameter):
              self.AP = JuMEG_wxArgvParserIO(self.PanelA.Panel,ShowCloseButton=True,**command)
              self.AP.update(ShowParameter=self.ShowParameter,ShowFileIO=self.ShowFileIO,ShowCloseButton=True)
              self.PanelA.Panel.GetSizer().Add(self.AP,1,wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,8)

              self.PanelA.Panel.SetAutoLayout(1)
              self.AP.FitInside()
              self.PanelA.Panel.Layout()

        self.GetParent().Layout()

    def ClickOnApply(self,evt):
        """
        ClickOnApply button sends
        :param evt: 
        :return: 
        """
        wx.LogMessage("ClickOnApply")
        wx.LogMessage(jb.pp_list2str(self.HostCtrl.HOST.GetHostInfo(),head="HOST Info"))

        cmd = self.AP.get_fullfile_command(ShowFileIO=self.ShowFileIO,ShowParameter=self.ShowParameter) #verbose=self.verbose)
        if self.verbose:
               wx.LogMessage(jb.pp_list2str(cmd, head="ArgParser Cmd: "))
               wx.LogMessage(jb.pp_list2str(self.HostCtrl.HOST.GetHostInfo(),head="HOST Info"))
        pub.sendMessage("SUBPROCESS.RUN.START",joblist=cmd,hostinfo=self.HostCtrl.HOST.GetHostInfo(),verbose=self.verbose)

        #except Exception as e:
        #    jb.pp(e,head="Error Exception")
        #    pub.sendMessage("MAIN_FRAME.MSG.ERROR",data="press <UPDATE> button and select a command")


    def ClickOnCancel(self,evt):
        pub.sendMessage("SUBPROCESS.RUN.CANCEL",joblist=[],hostinfo=self.HostCtrl.HOST.GetHostInfo(),verbose=self.verbose)
        #pub.sendMessage("MAIN_FRAME.MSG.INFO",data="<Cancel> button is no in use")

    def ClickOnButton(self, evt):
        obj = evt.GetEventObject()
        if obj.GetName().startswith("BT.APPLY"):
           self.ClickOnApply(evt)
        else:
           evt.Skip()
        
#----    
class JuMEG_GUI_ArgvParserFrame(JuMEG_MainFrame):
    """  """
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=wx.DefaultSize,name='JuMEG Argparser',*kargs,**kwargs):
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super(JuMEG_GUI_ArgvParserFrame,self).__init__(parent,id, title, pos, size, style, name,**kwargs)
        self.Center()
   #---
    def update(self,**kwargs):    
        """ 
        Results
        -------
        wxPanel obj e.g. MainPanel
        https://stackoverflow.com/questions/3104323/getting-a-wxpython-panel-item-to-expand  
        """
        return JuMEG_GUI_wxArgvParser(self,**kwargs )

    def UpdateAboutBox(self):
        self.AboutBox.description = "calling JuMEG python scripts with parsing arguments"
        self.AboutBox.version     = __version__
        self.AboutBox.copyright   = '(C) 2018 Frank Boers <f.boers@fz-juelich.de>'
        self.AboutBox.developer   = 'Frank Boers'
        self.AboutBox.docwriter   = 'Frank Boers'

if __name__ == '__main__':
   app    = wx.App()
   frame  = JuMEG_GUI_ArgvParserFrame(None,-1,'ARG Parser',ShowAll=True,ShowLogger=True,ShowCmdButtons=True,debug=True,verbose=True)
   app.MainLoop()
   
'''
/usr/bin/python2 /home/fboers/MEGBoers/programs/JuMEG/jumeg-py/jumeg-py-git-fboers-2018-11-19/jumeg/preproc/jumeg_preproc_noise_reducer.py --fif_filename=101716/MEG94T/121219_1310/1/101716_MEG94T_121219_1310_1_c,rfDC-raw.fif --fif_stage=/home/fboers/MEGBoers/data/exp/MEG94T/mne/ --exclude_artifacts --checkresults --verbose --run
'''


'''
    def __wx_init(self):
      #--- clear wx stuff
       for child in self.GetChildren():
           child.Destroy()

       self._pnl_command   = None
       self._pnl_argparser = None
       self._pnl_container = None
       self._pnl_buttons   = None
       self._pnl_logger    = None
       self._splitter      = None
       self._pnl_container = wx.Panel(self, -1)

      #--- show log stdout/stderr window
       if self.ShowLogger:
          self._splitter      = JuMEG_wxSplitterWindow(self,label="LOGGER") # from submenu Settings-> Looger
          self._pnl_logger    = JuMEG_wxLogger(self._splitter)
          #wx.Log.SetActiveTarget(JuMEG_wxLog(self,self._txtctrl))
          self._pnl_container = wx.Panel(self._splitter)
       else:
          self._pnl_container = wx.Panel(self)
       self._pnl_container.SetBackgroundColour("sky blue")

    def init_pubsub(self, **kwargs):
        pub.subscribe(self.update_wx_argparser,'COMMAND_UPDATE')
        pub.subscribe(self.ClickOnApply,self.GetName().upper()+".BT_APPLY")

    def __init_pubsub(self):
        """ """
       #--- APPLY
        pub.subscribe(self.ClickOnApply,'ARGV_PARSER.CLICK_ON_APPLY')
       #--- CANCEL
        pub.subscribe(self.ClickOnCancel,'ARGV_PARSER.CLICK_ON_CANCEL')
       #--- verbose
        pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
       #---
        pub.subscribe(self.ShowHelp,"MAIN_FRAME.CLICK_ON_HELP")
        pub.subscribe(self.SetVerbose,"COMMAND_FRAME_VERBOSE")
        #pub.subscribe(self.update_wx_argparser,'COMMAND_UPDATE')

    def ___ApplyLayout(self):
        ds1 = 3
      
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        if self._pnl_command:
           self.Sizer.Add( self._pnl_command,0, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,ds1)

       #--- split the window
        if self.ShowLogger:
           self._splitter.SplitHorizontally(self._pnl_container,self._pnl_logger,-100 )#self._pnl_container.GetSize()[0] )
           self.Sizer.Add( self._splitter,1,wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL,3)
        elif self.ShowParameter:
             self.Sizer.Add(self._pnl_container,1,wx.ALIGN_CENTER|wx.EXPAND|wx.ALL, ds1)

        if self._pnl_buttons:
            self.Sizer.Add(self._pnl_buttons, 0, wx.BOTTOM | wx.EXPAND | wx.ALL, ds1)

        self.SetSizer(self.Sizer)
        self.Fit()
        self.SetAutoLayout(1) 
        self.GetParent().Layout()
        
 def __update_wx_argparser(self,command=None):
       #--- update parser
        for child in self._pnl_container.GetChildren():
            child.Destroy()
        jb.pp(command,head="update_wx_argparser command")
        #try:
        if ( self.ShowFileIO or self.ShowParameter):
              self._pnl_argparser = JuMEG_wxArgvParserIO(self._pnl_container,**command)
              self._pnl_argparser.update(ShowParameter=self.ShowParameter,ShowFileIO=self.ShowFileIO)

              vbox = wx.BoxSizer(wx.VERTICAL)
              vbox.Add(self._pnl_argparser,1,wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,8)
              self._pnl_container.SetSizer(vbox)
              self._pnl_container.SetAutoLayout(1)
              self._pnl_argparser.FitInside()
              self._pnl_container.Layout()
        #except Exception as e:
        #     jb.pp(e,head="Error Exception in <JuMEG_GUI_wxArgvParser.update_wx_argparser>")
        #     pub.sendMessage("MAIN_FRAME.MSG.ERROR",msgtxt="in <UPDATE> command")

        self.GetParent().Layout()


       
class JuMEG_wxArgvParserButtons(wx.Panel):
    """
     shows Close,Cancel ... Apply button
     skip event send to parrent
    """
 #---     
    def __init__(self,parent,**kwargs):
        super(JuMEG_wxArgvParserButtons, self).__init__(parent)   
        self.update()
 #---
    def _update_buttons(self):
        """ generation wx.Button in a panel"""
        self._wxctrl_list_of_buttons =[]
        self._wxctrl_list_of_buttons.append(["CLOSE","BT.CLOSE",wx.ALIGN_LEFT,"Close program",None])
        self._wxctrl_list_of_buttons.append(["CANCEL","BT.CANCEL",wx.ALIGN_LEFT,"Cancel progress",None])
        self._wxctrl_list_of_buttons.append(["APPLY","BT.APPLY",wx.ALIGN_RIGHT,"Apply command",None])
        self._pnl_buttons = JuMEG_wxControlButtonPanel(self,label=None,control_list=self._wxctrl_list_of_buttons)
        self.Bind(wx.EVT_BUTTON, self.ClickOnButton)
 #--- 
    def _update_kwargs(self,**kwargs):
        self.use_pubsub    = kwargs.get("pubsub",True)
        self.verbose       = kwargs.get("verbose",False)               
 #---   
    def update(self,function=None,module=None,package=None,**kwargs):
        """ update """
        self._update_kwargs(**kwargs)
        self._update_buttons()
        self._ApplyLayout()
 #---      
    def _ApplyLayout(self):
        """set button panel"""
       
        # split the window
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self._pnl_buttons,0,wx.EXPAND,2)
        self.SetSizer(self.Sizer)
        self.Sizer.Fit(self)
        self.SetAutoLayout(1)
 #--- 
    def ClickOnButton(self,evt):
      """ skip event, send to parent"""
      obj = evt.GetEventObject()
      evt.Skip()




"cmd_buttons":{"All":False,"Close":False,"Cancel":True,"Apply":True}}     
   
      if kwargs.get("ShowCMDButtons",False):
           for k in self._param["cmd_buttons"].keys():
               self._param["cmd_buttons"][k]=True
        self.ShowCMDClose = kwargs.get("ShowCloseButton", self.ShowCloseButton)
  @property
    def ShowCloseButton( self ): return self._get_param("cmd_buttons", "Close")

      
'''