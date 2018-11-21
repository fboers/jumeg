#!/usr/bin/env python3
# -+-coding: utf-8 -+-

""" JuMEG preprocessing GUI based on mne-python
#- Exporting 4D data to FIF
- Merging MEG and EEG data
#- NoisyChannel detection
#- Artifact cleaning ICA
#- filtering
- Setting up experiment template structure
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

import wx
from   wx.lib.pubsub import pub
import wx.lib.scrolledpanel as scrolled

#--- jumeg cls
#from jumeg.jumeg_base                                     import jumeg_base as jb
#--- jumeg wx stuff
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_frame           import JuMEG_MainFrame
from jumeg.gui.jumeg_gui_meeg_merger                      import JuMEG_wxMEEGMergerPanel

#from jumeg.gui.wxlib.jumeg_gui_wxlib_main_panel           import JuMEG_wxMainPanel
#from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxSplitterWindow,JuMEG_wxCMDButtons,JuMEG_wxControlGrid,JuMEG_wxControlButtons,JuMEG_wxControlButtonPanel
#--- Merger CTRLs
#from jumeg.gui.wxlib.jumeg_gui_wxlib_experiment_template  import JuMEG_wxExpTemplate
#from jumeg.gui.wxlib.jumeg_gui_wxlib_id_selection_box     import JuMEG_wxIdSelectionBox

#from jumeg.gui.utils.jumeg_gui_utils_io                   import JuMEG_UtilsIO_PDFs
#---
#from jumeg.gui.wxlib.jumeg_gui_wxlib_pbshost              import JuMEG_wxPBSHosts
#from jumeg.gui.jumeg_gui_wx_argparser                     import JuMEG_GUI_wxArgvParser
#---
#from jumeg.ioutils.jumeg_ioutils_subprocess               import JuMEG_IoUtils_SubProcess

#from jumeg.gui.jumeg_gui_meeg_merger  import JuMEG_wxMEEGMergerPanel

__version__="2018-11-18-001"



class JuMEG_wxPreProcPanel(wx.Panel):
    """
    Parameters:
    ----------
    Results:
    --------
    wx.Panel

    """

    def __init__(self,parent,**kwargs):
        super().__init__(parent)
     #--- wxPanel CLS

        #self.SubProcess = JuMEG_IoUtils_SubProcess() # init and use via pubsub
        self._proc_list =["Export To FIF","Experiment Template","MEEG Merger","Noise Reducer","ICA","Epocher","Tools"]
        self._color_list =[wx.RED,wx.BLUE,wx.GREEN,wx.LIGHT_GREY,wx.CYAN,wx.YELLOW]

        self.update(**kwargs)
        self._ApplyLayout()


    @property
    def process_list(self): return self._proc_list

    def _get_param(self,k1,k2):
        return self._param[k1][k2]
    def _set_param(self,k1,k2,v):
        self._param[k1][k2]=v

    def SetVerbose(self, value=False):
        self.verbose = value

    def ShowHelp(self):
        print(self.__doc__)

    def _wx_init(self):  #--- clear wx stuff
       for child in self.GetChildren():
           child.Destroy()

     #--- command logger
      # self._splitter   = JuMEG_wxSplitterWindow(self,label="LOGGER") # from submenu Settings-> Looger
      # self._pnl_logger = JuMEG_wxLogger(self._splitter)

     #--- Notebook
       self._pnl_container = wx.Panel(self)
       self._pnl_container.SetBackgroundColour("sky blue")
       self.NB = wx.Notebook(self,-1,style=wx.BK_DEFAULT)


       i=0
       self._proc_pnl=dict()
       for p in self.process_list:
           self._proc_pnl[p]=None
       self._proc_pnl["MEEG Merger"] = JuMEG_wxMEEGMergerPanel(self.NB)

       for p in self.process_list:
           if not self._proc_pnl[p]:
              self._proc_pnl[p] = wx.Panel(self.NB,name=p)
              self._proc_pnl[p].SetBackgroundColour(self._color_list[i])
              i += 1
           self.NB.AddPage(self._proc_pnl[p],p)

       # self.NB.AddPage( MyPanel(self,-1),"TEST" )

       vbox=wx.BoxSizer(wx.VERTICAL)
       vbox.Add(self.NB,1,wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,3)
       self._pnl_container.SetSizer(vbox)
       self._pnl_container.SetAutoLayout(1)
       self._pnl_container.Fit()

    def _init_pubsub(self):
        """ """
       #--- verbose
        pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
       #---
        pub.subscribe(self.ShowHelp,"MAIN_FRAME.CLICK_ON_HELP")

    def _update_from_kwargs(self,**kwargs):
        self.SetBackgroundColour(kwargs.get("bg","grey88"))

    def update(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        self._wx_init()
        self._init_pubsub()

    def _ApplyLayout(self):
        ds1 = 3

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
       #--- split the window
       # self._splitter.SplitHorizontally(self._pnl_container, self._pnl_logger,
       #                                  -100)  # self._pnl_container.GetSize()[0] )

        self.Sizer.Add(self._pnl_container,1,wx.ALIGN_CENTER|wx.EXPAND|wx.ALL,3)

        #self.Sizer.Add( self._splitter,1,wx.ALIGN_CENTER_HORIZONTAL|wx.EXPAND|wx.ALL,3)

        self.SetSizer(self.Sizer)
        self.Sizer.Fit(self)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()

#----

class JuMEG_GUI_PreProcFrame(JuMEG_MainFrame):
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=[1024,768],name='JuMEG PreProc',*kargs,**kwargs):
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super().__init__(parent,id, title, pos, size, style, name,**kwargs)
        self.template_path = None
        self.verbose       = False
   #---
    def _update_kwargs(self,**kwargs):
        self.verbose = kwargs.get("verbose",self.verbose)
   #---
    def wxInitMainMenu(self):
        """
        overwrite
        add change of LoggerWindow position horizontal/vertical
        """
        pass
        #self.MenuBar.DestroyChildren()
        #self._init_MenuDataList()
        #self._update_menubar()
        # self.AddLoggerMenu(pos=1,label="Logger")
   #---
    def update(self,**kwargs):
       #---
        self.UpdateAboutBox()
       #---
        #self._init_MenuDataList()
       #---
        return JuMEG_wxPreProcPanel(self,name="JuMEG_PREPROC_PANEL",**kwargs)
   #---
    def wxInitStatusbar(self):
        self.STB = self.CreateStatusBar(4)
        #self.STB.SetStatusStyles([wx.SB_RAISED,wx.SB_SUNKEN,wx.SB_RAISED,wx.SB_SUNKEN])
        self.STB.SetStatusWidths([-1,1,-1,4])
        self.STB.SetStatusText('Experiment',0)
        self.STB.SetStatusText('Path',2)
   #---
    def UpdateAboutBox(self):
        self.AboutBox.name        = self.GetName() #"JuMEG MEEG Merger INM4-MEG-FZJ"
        self.AboutBox.description = self.GetName()#"JuMEG MEEG Merger"
        self.AboutBox.version     = __version__
        self.AboutBox.copyright   = '(C) 2018 Frank Boers'
        self.AboutBox.developer   = 'Frank Boers'
        self.AboutBox.docwriter   = 'Frank Boers'

if __name__ == '__main__':

   app = wx.App()
   frame = JuMEG_GUI_PreProcFrame(None,-1,'JuMEG PreProc FZJ-INM4',module="jumeg_merge_meeg",debug=True,verbose=True)
   app.MainLoop()













class JuMEG_GUI_PreProcFrame(JuMEG_MainFrame):
    """  """
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=(640,480),name='JuMEG',*kargs,**kwargs):
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super(JuMEG_GUI_PreProcFrame,self).__init__(parent,id, title, pos, size, style, name,**kwargs)
        self.Center()
   #---
    def _init_AboutBox(self):
        self.AboutBox.name        = self.GetName() #"JuMEG MEEG Merger INM4-MEG-FZJ"
        self.AboutBox.description = self.GetName()#"JuMEG MEEG Merger"
        self.AboutBox.version     = __version__
        self.AboutBox.copyright   = '(C) 2018 Frank Boers'
        self.AboutBox.developer   = 'Frank Boers'
        self.AboutBox.docwriter   = 'Frank Boers'

    def wxInitMainMenu(self):
        """
        overwrite
        add change of LoggerWindow position horizontal/vertical
        """
        self.MenuBar.DestroyChildren()
        self._init_MenuDataList()
        self._update_menubar()
        self.AddLoggerMenu(pos=1,label="Logger")
   #---
    def update(self,**kwargs):
        """
        place to write your code/controls

        Results
        -------
        wxPanel obj e.g. Main-Panel
        https://stackoverflow.com/questions/3104323/getting-a-wxpython-panel-item-to-expand
        """
       #--- add your controls
        self.JPP = JuMEG_GUI_wxPreProc(self,**kwargs)
        if self.debug:
            self.JPP.NB.SetSelection(1)

       #--- init flags
        if self.use_pubsub:  # verbose,debug
           pub.sendMessage('MAIN_FRAME.VERBOSE', value=kwargs.get("verbose"))
           pub.sendMessage('MAIN_FRAME.DEBUG',   value=kwargs.get("debug"))

        return self.JPP
   #---
    def wxInitStatusbar(self):
        self.STB = self.CreateStatusBar(4)
        #self.STB.SetStatusStyles([wx.SB_RAISED,wx.SB_SUNKEN,wx.SB_RAISED,wx.SB_SUNKEN])
        self.STB.SetStatusWidths([-1,1,-1,4])
        self.STB.SetStatusText('Experiment',0)
        self.STB.SetStatusText('Path',2)

if __name__ == '__main__':
   app    = wx.App()
   frame  = JuMEG_GUI_PreProcFrame(None,-1,'PreProc  Utility',debug=True,verbose=True)
   app.MainLoop()
