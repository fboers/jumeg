#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 19.05.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,sys,argparse
import wx
import wx.lib.scrolledpanel as scrolled

from pubsub import pub
from jumeg.base.ioutils.jumeg_file_reader import FileList

#from jumeg.gui.jumeg_gui_config                           import JuMEGConfig
from jumeg_gui_config                           import JuMEGConfig

from jumeg.gui.wxlib.jumeg_gui_wxlib_main_base            import JuMEGBaseFrame,JuMEGBaseMainPanel,JuMEGBasePanel,ShowFileDLG,LEA
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import ButtonPanel#,BasePanel

from jumeg.gui.wxlib.jumeg_gui_wxlib_logger import JuMEG_wxLogger
    # SpinCtrlScientific,EditableListBoxPanel,JuMEG_wxSTXTBTCtrl

__version__="2020-06-16-001"


class ConfigCtrl(JuMEGBasePanel):
    
    def _wx_init(self,**kwargs):
        self._CFG = JuMEGConfig(self,fname=kwargs.get("config"),ShowButtons=False)
    
    def _ApplyLayout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self._CFG,1,wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.ALL,5)
        self.SetSizer(vbox)
    
    def _init_pubsub(self):
       # pub.subscribe(self.ClickOnConfig,"MSG.CONFIG")
       pass
    
    def GetData(self):
        return self._CFG.GetData()
        
    def ClickOnConfig(self,data,config=None):
        if config:
            self._CFG._init_cfg(config=config)
            self._CFG.Show()
            self._CFG.Layout()
            self.Layout()
        elif data == "OPEN":
            self._CFG.ClickOnOpenConfigFile()
            if self._CFG.IsShown() == False:
                self._CFG.Show(True)
                self._CFG.Show()
                self._CFG.Layout()
                self.Layout()
        elif data == "SAVE":
            if self._CFG.IsShown():
                self._CFG.ClickOnSaveConfigFile()
            else:
                wx.LogMessage("No Config dict to save")


class FileSelectionBox(JuMEGBasePanel):
    """
    """
    def __init__(self,parent,**kwargs):
        super().__init__(parent,**kwargs)
    
    def _init(self,**kwargs):
        self.title     = "JuMEG ListFile INM4-MEG FZJ"
        self._FSC      = None
        self._FSB      = None
        self._pnl      = None
   
        self._pdfs     = list()
        self._ids      = None
        self._subjects = None
        self._ckbox    = None
        self._selected_items = 0
        self._font     = wx.Font(10,wx.FONTFAMILY_TELETYPE,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_NORMAL)
        self._FileReader = FileList()

    @property
    def FileReader(self):           return self._FileReader
    @property
    def FileSelectionBox(self):     return self._FSB
    @property
    def FileSelectionCounter(self): return self._FSC

    def update_files(self,fname):
        self.FileReader.read_file(fname)
    
    @property
    def n_pdfs(self): return len( self._pdfs )
    
    @property
    def pdfs(self): return self._pdfs
    @pdfs.setter
    def pdfs(self,v):
        if not v:
           self.clear()
           return
        if isinstance(v,(list)):
           self._pdfs     = v
        else:
           self._pdfs  = list(v)
           
        self._ids      = list()
        self._subjects = dict()
        for idx in range(self.n_pdfs):
            pdf = os.path.basename( self._pdfs[idx] )
            id  = pdf.split("_")[0]
            if not id in self._subjects:
               self._subjects[id] = list()
               self._ids.append(id)
            self._subjects[id].append(idx)
        self._ids.sort()
        
    @property
    def ids(self):      return self._ids
    @property
    def subjects(self): return self._subjects
    @property
    def n_subjects(self): return len( self._subjects )
   
    def _wx_init(self,**kwargs):
        self.SetBackgroundColour( kwargs.get("bg","grey80"))
       # -- file selection counter
        self._FSC = wx.StaticText(self, wx.ID_ANY,style=wx.ALIGN_RIGHT)
       # --
        self._font = kwargs.get("font",self._font)
        self._pnl  = scrolled.ScrolledPanel(self,-1,style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER)
        self._pnl.SetBackgroundColour(kwargs.get("bg","grey90"))
        
        self.Bind(wx.EVT_CHECKBOX,self.ClickOnCheckBox)
        self.update()
        self.load_from_file(list_path=kwargs.get("list_path"),list_name=kwargs.get("list_name"))
       
    def load_from_file(self,list_path=None,list_name=None):
        if list_name:
            if list_path:
               list_name = os.path.join(list_path,list_name)
            wx.CallAfter( self.FileReader.open, list_name )
    
    def _init_pubsub(self):
        pub.subscribe(self.ClickOnFile,"MSG.FILE")
        pub.subscribe(self.update,self.FileReader.name)
        pub.subscribe(self.DeSelectFiles,"BUTTON.DE/SELECT")
 
    def OpenFile(self,fname=None,showDLG=False):
        """
        Parameters
        ----------
        fname
        showDLG

        Returns
        -------
        list file name
        """
        if fname:
           p = os.path.dirname(fname)
           f = os.path.basename(fname)
        else:
           f = self.FileReader.basename
           p = self.FileReader.dirname
           
           showDLG = True
           
        if showDLG:
           fname = ShowFileDLG(self,title=self.title,style=wx.FD_OPEN,defaultDir=p,defaultFile=f)
        if fname:
           self.FileReader.open(fname)
        return fname
    
    def SaveSelectedFiles(self,fname=None,showDGL=False,auto_fname=False):
        """
        
        Parameters
        ----------
        fname
        showDGL
        auto_fname

        Returns
        -------

        """
        if self._selected_items < 1 :
           pub.sendMessage("MSG.WARNING",data="Can not save items to file\nPlease select items first")
           return
        
        if (not fname) and (not auto_fname):
           showDGL = True
        if auto_fname:
           fname = self.FileReader.get_auto_fname( flist=self.GetSelectedFiles() )
        
        fout = fname
        
        if showDGL:
           if fname:
              p = os.path.dirname(fname)
              f = os.path.basename(fname)
           else:
              p = self.FileReader.dirname
              f = self.FileReader.basename
           fout = ShowFileDLG(self,style=wx.FD_SAVE,defaultDir=p,defaultFile=f)
        if fout:
           if self.verbose:
              msg=["saving selected files: {} / {}".format(self._selected_items,self.n_pdfs),
                   "  -> fin : {}".format(fname),
                   "  -> fout: {}".format(fout)]
              wx.LogMessage( "\n".join(msg) )
           fout = self.FileReader.save(fout,flist=self.GetSelectedFiles())
           wx.LogMessage("done saving selected files")
           return fout

    def ClickOnFile(self,data):
        if data == "OPEN":
            self.OpenFile(showDLG=True)
        elif data.startswith("SAVE"):
            self.SaveSelectedFiles(showDGL=True)

    def ClickOnCheckBox(self,evt):
        obj = evt.GetEventObject()
        if obj.GetValue():
           self._selected_items+=1
        else:
           self._selected_items -= 1
           
        if self._selected_items < 0:
           self._selected_items = 0
        elif self._selected_items > self.n_pdfs:
           self._selected_items = self.n_pdfs
           
        self._update_file_selection_counter()
  
    def clear(self):
        """
        destroy all ck ctrls & reset PDFs
        :return:
        """
        for child in self._pnl.GetChildren():
            child.Destroy()
        self._pdfs     = list()
        self._ids      = list()
        self._subjects = dict()
        self._ckbox    = list()
        self._selected_items = 0
        self._FSC.SetLabel("0 / 0")
        
        #self.GetParent().Layout()
        
        
    def update(self,data=None,clear=True):
        """
        """
        # wx.LogMessage(" -> update file list: {}".format(self.FileReader.filename))

        if clear:
           self.clear()
        if data:
           self.pdfs = data
        else:
           return
          
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        LEA = wx.LEFT | wx.EXPAND | wx.ALL
        ds = 5
        for id in self.ids:
            for idx in self.subjects[id]:
                fname = os.path.basename( self.pdfs[idx] )
              # --- init pdf checkbox
                ckb = wx.CheckBox(self._pnl,label=fname,name="CK." + id+ '.' + str(idx))
                ckb.SetValue(True)
                ckb.SetForegroundColour(wx.BLACK)
                ckb.SetFont(self._font)
                ckb.SetToolTip( wx.ToolTip(self.pdfs[idx]) )
                self._ckbox.append(ckb)
                vbox.Add(ckb,0,LEA,ds)
               
            # --
            vbox.Add(wx.StaticLine(self._pnl),0,wx.LEFT | wx.EXPAND | wx.ALL)

        self._selected_items = self.n_pdfs
        self._update_file_selection_counter()
        
        self._pnl.SetSizer(vbox)
        self._pnl.SetupScrolling()
        
        self.Update()
        self.Refresh()
        self.GetParent().Layout()

    def _update_file_selection_counter(self):
        v = "{} / {}".format(self._selected_items,self.n_pdfs )
        self._FSC.SetLabel(v)

    def _ApplyFinalLayout(self):
        ds = 5
        LEA = wx.LEFT | wx.EXPAND | wx.ALL
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self._FSC,0,LEA,ds)
        if self._pnl:
           self._pnl.SetupScrolling()
           vbox.Add(self._pnl,1,LEA,ds)
    
        self.SetSizer(vbox)
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()
    
        self.Update()
        self.Refresh()
        self.GetParent().Layout()
       
   
    def Deselect(self,idx):
        try:
            self._ckbox[idx].SetValue(False)
        except:
            wx.LogError("ERROR: No such index in FileCheckBox: {}".format(idx))

    def GetSelections(self):
        indices=[]
        ick = 0
        for id in self.ids:
            for idx in self.subjects[id]:
                if self._ckbox[ick].GetValue():
                   indices.append(idx)
                ick += 1
                   
        return indices
       

    def GetSelectedFiles(self):
        f = self.FileReader.get_files( self.GetSelections() )
        # wx.LogMessage( "---> selected files:\n {}".format( "\n".join(f) ) )
        return f
    
    def DeSelectFiles(self,data):
        if self._selected_items:
            self._selected_items = 0
            status = False
            
        else:
            self._selected_items = self.n_pdfs
            status = True
           
        for cb in self._ckbox:
            cb.SetValue(status)
       
        self._update_file_selection_counter()
       
     
class MainPanel(JuMEGBaseMainPanel):
  
    def _init_pubsub(self):
        self._BUT.BindCtrls(self.ClickOnButton)
       
    def _wx_init(self,**kwargs):
        self._SPW_H = wx.SplitterWindow(self.MainPanel)
        self._FSB   = FileSelectionBox(self._SPW_H,**kwargs)
        self._CFG  = JuMEGConfig(self._SPW_H,fname=kwargs.get("config"),ShowButtons=False)
        # self._ConfigCtrl = ConfigCtrl(self._SPW_H,**kwargs)
        
        self._SPW_H.SplitVertically(self._FSB,self._CFG)
        self._SPW_H.SetSashGravity(0.5)

        self._BUT = ButtonPanel(self,name="BUTTON",labels=["Close","De/Select","Info","TEST","Cancel","Apply"],StretchSpacers=[0,0,0,1,0,0])
        
    def _ApplyLayout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self._SPW_H,1,LEA,2)
        self.MainPanel.SetSizer(vbox)
  
    def ClickOnButton(self,data=None):
        if data.upper().endswith("DE/Select"):
           self._FSB.DeSelectdFiles()
        elif data.upper().endswith("APPLY"):
           
           #-- ToDo
           #-- save selected files to tmp listfile
           #-- save config to tmp datafile
           #-- subprocess cmd @HOST
           #-- chek for cancel via thread
           #--- enabel cancel, disable Apply ??? multi proc on PBS
           try:
               flist = self._FSB.SaveSelectedFiles(auto_fname=True)
               f = self._FSB.GetSelectedFiles()
               wx.LogMessage("APPLY:\n -> listfile: {}\n -> selected files: {}\n -> {}".format(flist,len(f),"\n -> ".join(f)))
              
               fcfg = self._CFG.SaveConfigFile(fname=flist)
               data = self._CFG.GetData(pretty=True)
               wx.LogMessage("config data:\n -> {}".format(data))
               wx.LogMessage("APPLY:\n -> configfile: {}".format(fcfg))
               wx.LogMessage(" -> data:\n{}\n".format(data))
               
              # cmd = "-c "+fcfg +" -lname "+flist +" -s "stage +" -r -v"
               cmd = "-c "+fcfg +" -lname "+flist  +" -r -v"
               wx.LogMessage(" -> cmd: {}\n".format(cmd))
               
           except:
               wx.LogFatalError("ERROR in APPLY")
           
           
class JuMEGMenu(wx.MenuBar):
    def __init__(self,parent,**kwargs):
        super().__init__()
       #--- new TSV Event IDs
        wx.ID_CFG_OPEN,wx.ID_CFG_SAVE = wx.NewIdRef(count=2)

        self._init_m_file()
        self._init_m_config()
        self._init_m_settings()
        self._init_m_info()
        self._init_m_about()

        parent.SetMenuBar(self)

    def _init_m_file(self):
        """ file I/O """
        m_file = wx.Menu()
        m_file.Append(wx.ID_OPEN,'&Open')
        m_file.Append(wx.ID_SAVE,'&Save')
        m_file.AppendSeparator()
        m_file.Append(wx.ID_EXIT,'&Exit')
       # -- bind
        m_file.Bind(wx.EVT_MENU,self.ClickOnFile)
       
        self.Append(m_file,'&File List')

    def _init_m_config(self):
        """ config file """
        m_cfg = wx.Menu()
        m_cfg.Append(wx.ID_CFG_OPEN,'&Open')
        m_cfg.Append(wx.ID_CFG_SAVE,'&Save')
        m_cfg.Bind(wx.EVT_MENU,self.ClickOnConfig)
        self.Append(m_cfg,"&Config")

    def _init_m_settings(self):
        pass
    
    def _init_m_info(self):
        """ info / flags"""
        m_info = wx.Menu()
        m_info.Append(wx.ID_VERBOSE,"&Verbose",'set verbose',kind=wx.ITEM_CHECK)
        m_info.Append(wx.ID_DEBUG,"&Debug",'set debug',kind=wx.ITEM_CHECK)
        m_info.Bind(wx.EVT_MENU,self.ClickOnInfo)
        self.Append(m_info,'&Info')
  
    def ClickOnFile(self,evt):
        id = evt.GetId()
        if id == wx.ID_OPEN:
            self._send_msg("FILE","OPEN")
        elif id == wx.ID_SAVE:
            self._send_msg("FILE","SAVE")
        #elif id == wx.ID_SAVEAS:
        #    self._send_msg("FILE","SAVE AS")
        elif id == wx.ID_EXIT:
            self._send_msg("EXIT")
        else:
            evt.skip()

    def ClickOnConfig(self,evt):
        id = evt.GetId()
        if id == wx.ID_CFG_OPEN:
           self._send_msg("CONFIG","OPEN")
        elif id == wx.ID_CFG_SAVE:
           self._send_msg("CONFIG","SAVE")
        #elif id == wx.ID_CFG_SAVEAS:
        #   self._send_msg("CONFIG","SAVE AS")
        else:
            evt.skip()
    
    def ClickOnInfo(self,evt):
        id = evt.GetId()
        obj= evt.GetEventObject()
        m_item = obj.FindItemById(id)
        
        if id == wx.ID_VERBOSE:
           self._send_msg("VERBOSE",m_item.IsChecked())
        elif id == wx.ID_DEBUG:
           self._send_msg("DEBUG",m_item.IsChecked())
        else:
           evt.skip()

    def _send_msg(self,msg,*args):
        """
         call  pub.sendMessage,"MSG."+msg,data=args[0]
          e.g. MSG.FILE data="LOAD"
        Parameters
        ----------
        msg
        args

        Returns
        -------
         None
        """
        #wx.LogMessage("MSG.{} data: {}".format(msg,args))
        if args:
           wx.CallAfter( pub.sendMessage,"MSG."+msg,data=args[0])
        else:
           wx.CallAfter(pub.sendMessage,"MSG." + msg)
    
    def _init_m_about(self):
        pass
    
    def _init_pubsub(self,**kwargs):
        pass


class MainWindow(JuMEGBaseFrame):
    """
    stage,list_path,list_name,config,verbose)
    """
   # def __init__(self,parent,title,**kwargs):
   #     super().__init__(parent,-1,title,**kwargs)
    
    # -- ToDo set stage in ToolBar
    #stage = opt.stage
    #list_path = opt.list_path
    #list_name = opt.list_name\

    def _wx_init(self,**kwargs):
        self._MAIN_PNL = MainPanel(self,**kwargs)
        JuMEGMenu(self)
   
 
    def AboutBox(self):
        self.AboutBox.description = "JuMEG GUI INM4/MEG FZJ"
        self.AboutBox.version = __version__
        self.AboutBox.copyright = '(C) 2020 Frank Boers <f.boers@fz-juelich.de>'
        self.AboutBox.developer = 'Frank Boers'
        self.AboutBox.docwriter = 'Frank Boers'



def get_args(argv,parser=None,defaults=None,version=None):
    """
    get args using argparse.ArgumentParser ArgumentParser
    e.g: argparse  https://docs.python.org/3/library/argparse.html

    :param argv:   the arguments, parameter e.g.: sys.argv
    :param parser: argparser obj, the base/default obj like --verbose. --debug
    :param version: adds version to description
    :return:

    Results:
    --------
     parser.parse_args(), parser
    """
    
    description = """
                  JuMEG Pipeline GUI
                  script version : {}
                  python version : {}

                  Example:

                  jumeg_gui_pipeline.py -c jumeg_config.yaml -lname test_meeg.txt -lpath .

                  """.format(version,sys.version.replace("\n"," "))
    
    h_stage = """
                      stage/base dir: start path for ids from list
                      -> start path to directory structure
                      e.g. /data/megstore1/exp/M100/mne/
                      """
    h_config = "script config file, full filename"
    h_lpath  = "path for list file, list of file to process containing list of full filenames"
    h_lname  = "list file name, list of file to process containing list of full filenames"
   
    h_verbose = "bool, str, int, or None"
    
    #--- parser
    if not parser:
        parser = argparse.ArgumentParser(description=description,formatter_class=argparse.RawTextHelpFormatter)
    else:
        parser.description = description
    
    if not defaults:
        defaults = { }

        #---  parameter settings  if opt  elif config else use defaults
    parser.add_argument("-s","--stage",help=h_stage)  #,default=defaults.get("stage",".") )
   # --
    parser.add_argument("-lpath","--list_path",help=h_lpath)
    parser.add_argument("-lname","--list_name",help=h_lname)
   # --
    parser.add_argument("-c","--config",help=h_config,default=defaults.get("config"))
   # -- flags
    parser.add_argument("-v","--verbose",action="store_true",help=h_verbose,default=defaults.get("verbose"))
  
    return parser_update_flags(argv=argv,parser=parser)

def parser_info():
    """
    show cmd line parameter
    """
    # https://stackoverflow.com/questions/39978186/python-print-all-argparse-arguments-including-defaults/39978305
    msg = ["input parameter:"]
    for k,v in sorted(vars(opt).items()): msg.append("  -> {0:12}: {1}".format(k,v))
    print("\n".join(msg))
    #return("\n".join(msg))


def parser_update_flags(argv=None,parser=None):
    """
    init flags
    check if flag is set in argv as True
    if not set flag to False
    problem can not switch on/off flag via cmd call

    :param argv:
    :param parser:
    :return:
    opt  e.g.: parser.parse_args(), parser
    """
    opt = parser.parse_args()
    for g in parser._action_groups:
        for obj in g._group_actions:
            if str(type(obj)).endswith('_StoreTrueAction\'>'):
                if vars(opt).get(obj.dest):
                    opt.__dict__[obj.dest] = False
                    for flg in argv:
                        if flg in obj.option_strings:
                            opt.__dict__[obj.dest] = True
                            break
    return opt,parser





class MainWindow(JuMEGBaseFrame):

    def _wx_init(self,**kwargs):
        self._MAIN_PNL = MainPanel(self,**kwargs)
        JuMEGMenu(self)

    def AboutBox(self):
        self.AboutBox.description = "JuMEG GUI INM4/MEG FZJ"
        self.AboutBox.version = __version__
        self.AboutBox.copyright = '(C) 2020 Frank Boers <f.boers@fz-juelich.de>'
        self.AboutBox.developer = 'Frank Boers'
        self.AboutBox.docwriter = 'Frank Boers'

    def Destroy(self):
        self._MAIN_PNL.close()
        super().Destroy()



#=========================================================================================
#==== MAIN
#=========================================================================================
if __name__ == "__main__":
   app  = wx.App()
   argv = sys.argv
   opt, parser = get_args(argv,version=__version__)
   #if len(argv) < 2:
   #   parser.print_help()
   #   sys.exit(-1)
   
   if opt.verbose:
      parser_info()
  
   # -c intext_config.yaml -lname intext_meeg.txt -lpath . -s /media/fboers/USB_2TB/exp/INTEXT/mne -r -v
   frame = MainWindow(None,'JuMEG GUI Pipeline INM4/MEG FZJ',
                      stage= opt.stage,list_path=opt.list_path,list_name=opt.list_name,config=opt.config,verbose=opt.verbose)
   frame.Show()
   app.MainLoop()
