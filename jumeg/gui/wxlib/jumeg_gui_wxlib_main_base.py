#!/usr/bin/env python3
# -+-coding: utf-8 -+-
"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 09.06.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

#-- FB
# import os,sys,argparse,pprint
import warnings
import wx
import wx.lib.scrolledpanel as scrolled
from pubsub         import pub

from jumeg.gui.wxlib.jumeg_gui_wxlib_logger import JuMEG_wxLogger


#--- new TSV Event IDs
wx.ID_VERBOSE,wx.ID_DEBUG = wx.NewIdRef(count=2)

LEA = wx.LEFT | wx.EXPAND | wx.ALL

__version__ = "2020-06-10-001"


def ShowFileDLG(parent,title="JuMEG",style=wx.FD_OPEN,wildcard="txt file (*.txt)|*.txt",defaultDir=".",defaultFile=""):
    """
    show wx.FileDialog as Open/Save Dlg

    Parameters
    ----------
    parent    : parent
    title     : <JuMEG>
    style     : wx.FD_OPEN  or wx.FD_SAVE
    wildcard
    defaultDir
    defaultFile

    Returns
    -------
    pat or file

    """
    if style == wx.FD_OPEN:
        txt = "Open File"
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
    else:
        txt = "Save File:"
        style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
    
    title += " " + txt
    if not defaultDir:
       defaultDir="."
    if not defaultFile:
       defaultFile=""
    dlg = wx.FileDialog(parent,title,defaultDir,defaultFile,wildcard=wildcard,style=style)
    #dlg.SetDirectory(os.path.dirname(fname))
    
    if dlg.ShowModal() == wx.ID_OK:
        return dlg.GetPath()
    
    return None


class JuMEGBasePanel(wx.Panel):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,style=wx.BORDER_SUNKEN)
        self._verbose = False
        self._debug   = False
        self.SetBackgroundColour(kwargs.get("bg","grey70"))
        self._init(**kwargs)
        
        self._wx_init(**kwargs)
        self._ApplyLayout()
        self._ApplyFinalLayout()
        self._on_init_pubsub()
        self._init_pubsub()
    
    @property
    def verbose(self): return self._verbose
    @verbose.setter
    def verbose(self,v):
        self._verbose = v
    
    def _init(self,**kwargs):
        pass
    
    def _wx_init(self,**kwargs):
        pass
    
    def ClickOnCtrl(self,evt):
        evt.Skip()
    
    def _ApplyLayout(self):
        """
        pack ctrls in sizer and set sizer
 
        Example
        --------
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(0,0,1,LA,5)
        self.SetSizer(hbox)
 
        Returns
        -------
        None.
 
        """
        pass
    
    def _on_init_pubsub(self):
        pub.subscribe(self._set_verbose,'MSG.VERBOSE')
        pub.subscribe(self._set_debug,'MSG.DEBUG')

    def _set_verbose(self,data=False):
        self.verbose = data
    def _set_debug(self,data=False):
        self.debug = data

    def _ApplyFinalLayout(self):
        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()
        
        self.Update()
        self.Refresh()
        self.GetParent().Layout()
    
    def _init_pubsub(self):
        pass

class JuMEGBaseMainPanel(wx.Panel):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,style=wx.BORDER_SUNKEN)
        
        self.SetBackgroundColour(kwargs.get("bg","grey70"))
       
        self._LOG   = None
        self._PNL   = None
        self._BUT   = None
        
        self._init(**kwargs)
        
        self._wx_on_enter_init()
        self._wx_init(**kwargs)
        self._wx_on_exit_init()
        
        self._ApplyLayout()
        self._ApplyFinalLayout()
        self._on_init_pubsub()
        self._init_pubsub()
        #self.Bind(wx.EVT_KEY_UP,self.ClickOnKey)
        #self.Bind(wx.EVT_CHAR_HOOK,self.ClickOnKey)
    @property
    def Logger(self): return self._LOG

    @property
    def MainPanel(self): return self._PNL

    @property
    def Buttons(self):   return self._BUT
    @property
    def verbose(self):   return self._verbose
    @verbose.setter
    def verbose(self,v):
        self._verbose = v
        
    def _set_verbose(self,data=False):
        self.verbose = data
    def _set_debug(self,data=False):
        self.debug = data

    def _on_init_pubsub(self):
        pub.subscribe(self._set_verbose,'MSG.VERBOSE')
        pub.subscribe(self._set_debug,'MSG.DEBUG')
     
    def _wx_on_enter_init(self):
        self._SPW_LOG = wx.SplitterWindow(self)
        self._SPW_LOG.SetSashGravity(0.8)
        
        self._LOG     = JuMEG_wxLogger(self._SPW_LOG)
        self._PNL     = wx.Panel(self._SPW_LOG)

    def _init(self,**kwargs):
        pass
    def _wx_on_exit_init(self):
        pass
     
    def _ApplyFinalLayout(self):
        if not self.GetSizer():
           self.SetSizer( wx.BoxSizer(wx.VERTICAL) )
        if self._SPW_LOG:
           self._SPW_LOG.SplitHorizontally(self._PNL,self._LOG)
           self.GetSizer().Add(self._SPW_LOG,1,LEA,5)
        if self._BUT:
           self.GetSizer().Add(self._BUT,0,LEA,5)

        self.SetAutoLayout(True)
        self.Fit()
        self.Layout()
   
   
class StatusBar(object):
    __slots__ = ["colour","_STB","_STATUS","_parent"]
    
    def __init__(self,parent,**kwargs):
        super().__init__()
        self._parent = parent
        self.colour = { "ok":'#E0E2EB',"busy":"YELLOW","changed":"ORANGE","error":"RED" }
        self._STB = None
        self._STATUS = True  # show/hide
        self._wx_init(**kwargs)
    
    @property
    def StatusBar(self):
        return self._STB
    
    def _wx_init(self,fields=8,width=[80,-1.6,-1.0,-1.9,40,80,150,80],status_style=wx.SB_SUNKEN):
        """

        :param fields: 8 Status,path,fname,bads,n-bads,time,size,nn
        :param w:
        :param status_style:
        :return:
        """
        if self._STB:
            self._STB.Destroy()
        self._STB = self._parent.CreateStatusBar(fields,style=wx.STB_DEFAULT_STYLE)
        self._STB.SetStatusWidths(width)
        st = []
        for i in range(len(width)):
            st.append(status_style)
        self._STB.SetStatusStyles(st)
    
    def SetMSG(self,msg):
        '''
         call from pubsub
         "MAIN_FRAME.STB.MSG", value=["RUN", self._args[0], "PID", str(self.__proc.pid)]
        '''
        idx = 0
        if not msg: return
        if not isinstance(msg,(list)): msg = list(msg)
        if msg:
            for s in msg:
                if s:
                    self._STB.SetStatusText(str(s),i=idx)
                idx += 1
                if idx >= self._STB.GetFieldsCount(): break
    
    def UpdateMSG(self,status="OK",msg=None):
        """

        :param status:
        :param msg:
        :return:
        """
        cl = self.colour.get(status.lower(),"error")
        self._STB.SetBackgroundColour(cl)
        if msg:
            self.SetMSG(msg)
        self._STB.Refresh()
    
    def _init_pubsub(self):
        """" init pubsub call and messages"""
        pub.subscribe(self.UpdateMSG,"MSG.STB")
    
    def toggle(self,status=-1):
        if status != -1:
            self._STATUS = status
        else:
            self._STATUS = not self._STATUS
        self._STB.Show(self._STATUS)


class JuMEGBaseMainMenu(wx.MenuBar):
    def __init__(self,parent,**kwargs):
        super().__init__()
        #--- file I/O
        mfile = wx.Menu()
        mfile.Append(wx.ID_OPEN,'&Open')
        mfile.Append(wx.ID_SAVE,'&Save')
        mfile.Append(wx.ID_SAVEAS,"Save_As")
        mfile.AppendSeparator()
        mfile.Append(wx.ID_EXIT,'&Exit')
        self.Append(mfile,'&File')
        #--- Settings
        msettings = wx.Menu()
        self.Append(msettings,"&Settings")
        
        #--- Flags
        minfo = wx.Menu()
        minfo.Append(wx.ID_VERBOSE,"&Verbose",'set verbose',kind=wx.ITEM_CHECK)
        minfo.Append(wx.ID_DEBUG,"&Debug",'set debug',kind=wx.ITEM_CHECK)
        self.Append(minfo,'&Info')
        #--- ? ABOUT, Help
        
        #--- bind
        parent.Bind(wx.EVT_MENU,kwargs.get("cmd",self.ClickOnMenu))
        parent.SetMenuBar(self)
    
    def _init_pubsub(self,**kwargs):
        pass
    
    def ClickOnMenu(self,evt):
        evt.skip()


class JuMEGBaseFrame(wx.Frame):
    __slots__ = ["_STB","_TB","_MAIN_PNL","_verbose","_debug","_menu_info","_menu_help","_combo_chops"]
    
    def __init__(self,parent,*kargs,**kwargs):
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super().__init__(parent,-1,*kargs)  #,**kwargs)
        # -- wx
        self._MAIN_PNL = None
        self._TB       = None
        self._STB      = None
        # -- flags
        self._debug   = False
        self._verbose = False
        # -- init wx
        self._on_init(**kwargs)
        self._wx_init(**kwargs)
        
       # self._wx_init_toolbar()
        self._wx_init_bind()
       
       #-- init pubsu
        self._on_init_pubsub()
        self._init_pubsub()
       # --
        self._update(**kwargs)
    
    @property
    def MainPanel(self): return self._MAIN_PNL
    
    @property
    def StatusBar(self):   return self._STB.StatusBar
    
    @property
    def ToolBar(self):     return self._TB
    
    @property
    def debug(self):      return self._debug
    @debug.setter
    def debug(self,v):
        if v:
            warnings.filterwarnings("ignore")
        else:
            warnings.filterwarnings("default")
        if v:
            self.verbose = v
        self._debug = v
        pub.sendMessage('MSG.DEBUG',data=v)
    
    @property
    def verbose(self):  return self._verbose
    @verbose.setter
    def verbose(self,v):
        self._verbose = v
        pub.sendMessage('MSG.VERBOSE',data=v)
    
    def _update_from_kwargs(self,**kwargs):
        pass
    
    def _update(self,**kwargs):
        pub.sendMessage("MSG.TEST",data={ 'fname':kwargs.get("fname"),'path':kwargs.get("path") })
    
 
    def _on_init(self,**kwargs):
        self.debug   = kwargs.get("debug",self.debug)
        self.verbose = kwargs.get("verbose",self.verbose)
        self.SetName(kwargs.get("name","JuMEG.TSV"))
       # --
        if not kwargs.get("size"):
            w,h = wx.GetDisplaySize()
            size = (w / 1.3,h / 1.3)
        self.SetSize(size)
        self.Center()
     
        # -- init menu
        # JuMEGBaseMainMenu(self,cmd=self.ClickOnMenu)
        # -- init STB in a new CLS
        self._STB = StatusBar(self)

        self.Bind(wx.EVT_CLOSE,self.ClickOnClose)
        self.Bind(wx.EVT_KEY_UP,self.ClickOnKey)
        self.Bind(wx.EVT_CHAR_HOOK,self.ClickOnKey)
        
    def _wx_init(self,**kwargs):
        self._MAIN_PNL = JuMEGBaseMainPanel(self,**kwargs)
        self._MAIN_PNL.SetBackgroundColour("blue")
    
    def _wx_init_bind(self):
        pass
    
    def OnExitApp(self,evt):
        self.ClickOnClose(evt)
    
    def ToggleCheckBox(self,evt):
        obj = evt.GetEventObject()
        v = obj.GetValue()
        name = obj.GetName().upper()
        if name.endswith("STATUSBAR"):
             self._STB.toggle()
        elif name.endswith("TOGGLEBAR"):
            self._TB.toggle()
        elif name.endswith("VERBOSE"):
            self.verbose = v
        elif name.endswith("DEBUG"):
            self.debug = v
            
    def GetEventObjName(self,evt):
        """
        Parameters
        ----------
        evt

        Returns
        -------
        name, obj
        """
        obj = evt.GetEventObject()
        return obj.GetName(),obj

    
    def ClickOnButton(self,evt):
        evt.Skip()
    
    def ClickOnControlKey(self,keycode):
        """
        use if <CONTROL> + <key> pressed
        Parameters
        ----------
        keycode: char
        
        if keycode == "S":
            pub.sendMessage("MSG.SHOW.SETTINGS")
        
        Returns
        -------
        None
        """
        pass

    def ClickOnSpecialKey(self,keycode):
        """
        use if <CONTROL> + <key> pressed
        Parameters
        ----------
        keycode: char
        
        if keycode == wx.WXK_F4:
            pub.sendMessage("MSG.TEST")
        Returns
        -------
        True / False
        """
        return False
    
    def ClickOnKey(self,evt):
        keycode = evt.GetKeyCode()
        
        #print("keycode: {}".format(keycode))
        
        #wx.LogMessage("keycode: {}".format(keycode))
        
        #--- ck for CRTL / SHIFT
        if wx.GetKeyState(wx.WXK_CONTROL):
            if not evt.GetUnicodeKey(): return  # no special keys F1 ...
            self.ClickOnControlKey( chr(keycode) )
        elif keycode == wx.WXK_F1:
            pub.sendMessage("MSG.SHOW.HELP")
        elif keycode == wx.WXK_F2:
            mb = self.GetMenuBar()
            mb.Show(not mb.Shown)
        elif keycode == wx.WXK_F3:
            if self.ToolBar:
               self.ToolBar.toggle()
        elif keycode == wx.WXK_F4:
            self.StatusBar.toggle()
        elif keycode == wx.WXK_ESCAPE:
            self.Close()
        elif not self.ClickOnSpecialKey(keycode):
            evt.Skip()

    def _init_pubsub(self):
        pass

    def _on_init_pubsub(self):
        """ init pubsub call and messages"""
        
        # --  MAIN_FRAME
        pub.subscribe(self.msg_error,"MSG.ERROR")
        pub.subscribe(self.msg_warning,"MSG.WARNING")
        pub.subscribe(self.msg_info,"MSG.INFO")
        # --
        pub.subscribe(self.OnBusy,"MSG.BUSY")
        # --
        pub.subscribe(self.ClickOnClose,"MSG.CLOSE")
        pub.subscribe(self.ClickOnClose,"MSG.EXIT")
        pub.subscribe(self.ClickOnClose,"BUTTON.CLOSE")
        
        # -- handle KEY events from sub panels / cls
        pub.subscribe(self.ClickOnKey,"MSG.EVENT.KEY_UP")
        # --
        pub.subscribe(self._set_verbose,'MSG.VERBOSE')
        pub.subscribe(self._set_debug,'MSG.DEBUG')

    def _set_verbose(self,data=False):
        self.verbose = data

    def _set_debug(self,data=False):
        self.debug = data

    def OnBusy(self,status="OK",msg=None):
        self._STB.UpdateMSG(status=status,msg=msg)
    
    def Show(self,show=True):
        #--- make sure  Frame is on screen and OGL is init
        super().Show(show=show)
       
    def AboutBox(self):
        self.AboutBox.description = "JuMEG GUI INM4/MEG FZJ"
        self.AboutBox.version = __version__
        self.AboutBox.copyright = '(C) 2020 Frank Boers <f.boers@fz-juelich.de>'
        self.AboutBox.developer = 'Frank Boers'
        self.AboutBox.docwriter = 'Frank Boers'
    
    def ClickOnHelp(self):
        pass
    
    def ClickOnAbout(self,evt):
        self.AboutBox.show(self)
    
    def ClickOnClose(self,*args,**kwargs):
        if not self.debug:
            if wx.MessageBox('Are you sure to quit?',"Please confirm",wx.ICON_QUESTION | wx.YES_NO) != wx.YES:
                return
        self.Destroy()
        if args:
           args[0].Skip()
    
    def msg_error(self,data="ERROR"):
        if isinstance(data,(list)):
            data = "\n".join(data)
        wx.MessageBox("Error: " + data,caption="ERROR  " + self.Name,style=wx.ICON_ERROR | wx.OK)
    
    def msg_warning(self,data="WARNING"):
        if isinstance(data,(list)):
            data = "\n".join(data)
        wx.MessageBox("Warning: " + data,caption="Warning  " + self.Name,style=wx.ICON_WARNING | wx.OK)
    
    def msg_info(self,data="INFO"):
        if isinstance(data,(list)):
            msgtxt = "\n".join(data)
        wx.MessageBox("Info: " + data,caption="Info  " + self.Name,style=wx.ICON_INFORMATION | wx.OK)


#=========================================================================================
#==== MAIN
#=========================================================================================
if __name__ == "__main__":
    app = wx.App()
    
    frame =JuMEGBaseFrame(None,-1,'JuMEG GUI TEST Base Frame INM4/MEG FZJ')
    frame.Show()
    app.MainLoop()