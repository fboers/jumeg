#!/usr/bin/envn python3
# -+-coding: utf-8 -+-
#----------------------------------------
# Created by fboers at 19.09.18
#----------------------------------------
# Update
#----------------------------------------

import wx
from wx.lib.pubsub import pub
from wx.lib.scrolledpanel import ScrolledPanel

from jumeg.gui.wxlib.jumeg_gui_wxlib_logger               import JuMEG_wxLogger
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxSplitterWindow #,JuMEG_wxControlButtonPanel,JuMEG_wxControls,JuMEG_wxControlIoDLGButtons,JuMEG_wxControlGrid,

version="2018.09.19.001"

class JuMEG_wxPanel(wx.Panel):
    '''
    JuMEG_wxPanel  base CLS for JuMEG wx.Panels
    with functions to ovewrite to avoid overhead

    Paremeters:
    -----------
     bg        : backgroundcolor <grey88>
     verbose   : <verbose>
     debug     : <debug>
     ShowLogger: <False>

    Functions to overwrite:
    -----------------------
     update_from_kwargs(**kwargs)
     wx_init(**kwargs)
     init_pubsub(**kwargs)
     update(**kwargs)

    Layout function
    ----------------
    ApplyLayout()   use <self.MainPanel> to pack you controls

    Example:
    --------
    class JuMEG_wxMEEGMerger(JuMEG_wxPanel):
          def __init__(self, parent, **kwargs):
             super(JuMEG_wxMEEGMerger, self).__init__(parent)
             self._init(**kwargs) # here is the initialization

          def ApplyLayout(self):
              """ use PanelA and PanelB to put the contrls and to split between """
              ds = 4
             #--- fill PanelA with controls
              vboxA = wx.BoxSizer(wx.VERTICAL)
              vboxA.Add(self.CtrlA1, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, ds)
              vboxA.Add((0, 0), 0, wx.ALIGN_RIGHT | wx.ALL)
              hboxA = wx.BoxSizer(wx.HORIZONTAL)
              hboxA.Add(self.CtrlA2, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, ds)
              hboxA.Add(self.CtrlA3, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, ds)
              vboxA.Add(hboxA, 1, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL)
              self.PanelA.SetSizer(vboxA)
             #--- fill PanelB with controls
              vboxB = wx.BoxSizer(wx.VERTICAL)
              vboxB.Add(self.CtrlB1, 0, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, ds)
              self.PanelB.SetSizer(vboxB)

              self.SplitterAB.SplitVertically(self.PanelA,self.PanelB)

    '''
    def __init__(self,*kargs,**kwargs):
        super(JuMEG_wxPanel,self).__init__(*kargs,id=wx.ID_ANY,style=wx.SUNKEN_BORDER,**kwargs)
        self._splitter  = None
        self.use_pubsub = True
        self.debug      = False
        self.verbose    = False
        self._param     = {}
        self.__isInit   = False
        self.__isMinimize = False
      # self._init(**kwargs) # the function to call in child class

    def _get_param(self,k1,k2):
        return self._param[k1][k2]
    def _set_param(self,k1,k2,v):
        self._param[k1][k2]=v

    @property
    def isInit(self): return self.__isInit

    @property
    def WindowSplitter(self): return self._splitter

    @property
    def LoggerPanel(self):return self._pnl_logger

    @property
    def MainPanel(self):  return self._pnl_main

    @property
    def ShowLogger(self)  : return self._show_logger
    @ShowLogger.setter
    def ShowLogger(self,v): self._show_logger = v

    def SetVerbose(self,value=False):
        self.verbose=value

    def ShowHelp(self):
        """ show help __doc__string"""
        #---ToDo show within wx.DLG
        print(self.__doc__)

#--- default methods
    def _update_from_kwargs_default(self,**kwargs):
        self.ShowLogger = kwargs.get("ShowLogger", False)
        self.verbose    = kwargs.get("verbose", False)
        self.debug      = kwargs.get("debug", False)
        self.SetBackgroundColour = kwargs.get("bg", "grey88")

    def _wx_init_default(self, **kwargs):
        """ window default settings"""
        self.clear_children(self)
        # --- init splitter for controls and logger
        self._splitter = None
        self._pnl_logger = None
        self._pnl_main = None
        # --- command logger
        if self.ShowLogger:
            self._splitter = JuMEG_wxSplitterWindow(self, label="Logger", name=self.GetName() + ".LOGGER",
                                                    listener=self.GetParent().GetName())
            self._pnl_logger = JuMEG_wxLogger(self._splitter, listener=self.GetParent().GetName())
            self._pnl_main = wx.Panel(self._splitter)
            self._pnl_main.SetBackgroundColour(wx.Colour(0, 0, 128))
        else:  # --- only you controls
            self._pnl_main = wx.Panel(self)
            self._pnl_main.SetBackgroundColour(wx.RED)

    def _init_pubsub_default(self):
        pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
        pub.subscribe(self.ShowHelp, self.GetName()+".SHOW_HELP")

#--- overwrite methods
    def update_from_kwargs(self,**kwargs):
        """ pass """
        pass

    def wx_init(self, **kwargs):
        """ init WX controls """
        pass

    def init_pubsub(self, **kwargs):
        """"
        init pubsub call
        pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')
        """
        pass

    def update(self, **kwargs):
        pass

    def ApplyLayout(selfself):
        """ your layout stuff """
        pass

  #--- init all
    def _init(self,**kwargs):
        if self.isInit:
           self.clear()
      #---
        self._update_from_kwargs_default(**kwargs)
        self.update_from_kwargs(**kwargs)
      #---
        self._wx_init_default()
        self.wx_init(**kwargs)
      #---
        self._init_pubsub_default()
        self.init_pubsub(**kwargs)
      #---
        self.update(**kwargs)
        self.__isInit=True
        self._ApplyLayout()

    def _ApplyLayout(self):
        """ default Layout Framework """
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.ApplyLayout() #-- fill PanelA amd PanelB with controls

        #vbox = wx.BoxSizer(wx.VERTICAL)
        #vbox.Add( self.SplitterAB,1,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,5 )
        #self.MainPanel.SetSizer(vbox)
        self.MainPanel.Fit()
        self.MainPanel.SetAutoLayout(1)

        if self.ShowLogger:
           self._splitter.SplitHorizontally(self.MainPanel,self.LoggerPanel)
           self._splitter.SetMinimumPaneSize(50)
           self._splitter.SetSashGravity(1.0)
           self._splitter.SetSashPosition(-50,redraw=True)
           self.Sizer.Add(self._splitter, 1, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)
        else:
           self.Sizer.Add(self.MainPanel, 1, wx.ALIGN_CENTER | wx.EXPAND | wx.ALL, 5)

        self.SetSizer(self.Sizer)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()

   #--- clear
    def clear_parameter(self):
        """ clear parameter overwrite"""
        pass

    def clear_children(self,wxctrl):
        """ clear/delete wx childeren """
        for child in wxctrl.GetChildren():
            child.Destroy()
        self.Layout()
        self.Fit()

    def clear(self,wxctrl=None):
        """ clear parameter and delete wx childeren """
        self.__isInit = False
        self.clear_parameter()
       #--- clear wx stuff
        self.clear_children(self)
