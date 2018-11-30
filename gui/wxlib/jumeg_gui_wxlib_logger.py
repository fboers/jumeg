import wx,sys,io
from wx.lib.pubsub import pub
from jumeg.jumeg_base  import jumeg_base as jb
__version__= "2018-11-15-001"

# change formatter
#log_fh = logging.FileHandler("error.log")
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
#log_fh.setFormatter(formatter)


class JuMEG_wxLog(wx.Log):
    '''
    from wxdemos main line 420 class MyLog(wx.Log)

    Parameter:
    ----------
    wx.TextCtrl
    logTime: 0

    ToDo filter warnings e.g.
     import warnings
     with warnings.catch_warnings():
     warnings.filterwarnings("ignore",category=DeprecationWarning)
     import mne

    '''
    def __init__(self, textCtrl, logTime=0):
        super().__init__()
        self._txtctrl         = textCtrl
        self.logTime          = logTime
        self._LogLevels       = [wx.LOG_Info, wx.LOG_Message, wx.LOG_Trace, wx.LOG_Warning, wx.LOG_Debug, wx.LOG_Error,wx.LOG_FatalError]
        self._LogLevelColours = [wx.BLACK, wx.BLACK, wx.BLACK, wx.GREEN, wx.BLUE, wx.RED,wx.RED]
        self.colour           = wx.BLACK

    def _scroll_to_end(self):
        """
        scrolls the txtctrl to the end
        https://stackoverflow.com/questions/47960619/set-insertionpoint-to-end-of-current-line-in-wxpython-wx-textctrl
        """
        curPos = self._txtctrl.GetInsertionPoint()
        curVal,curCol,curRow = self._txtctrl.PositionToXY(curPos)
        lineNum = curRow
        lineText = self._txtctrl.GetLineText(lineNum)
        newPos = self._txtctrl.XYToPosition(len(lineText), curRow)
        self._txtctrl.SetInsertionPoint(newPos)

    def LogLevelColour(self,level):
        idx = self._LogLevels.index(level)
        if not isinstance(idx,int):
           idx = 0
        return self._LogLevelColours[idx]

    def DoLogTextAtLevel(self,level,msg):
        """
        writing loglevel message with spcial loglevel-colour to text ctrl
        :param level: wx-loglevel [wx.LOG_Info, wx.LOG_Message,...]
        :param msg: message to display
        :param info: wx.LogRecordInfo
        :return:
        """

        if self._txtctrl:
           self._txtctrl.SetDefaultStyle(wx.TextAttr(self.LogLevelColour(level)))
           self._txtctrl.AppendText(msg + '\n')
           self._txtctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour))
           self._scroll_to_end()
           self._txtctrl.Refresh()
           self.Flush()
        else:
           print(msg)

class JuMEG_wxLogger(wx.Panel):
    """
     panel with wx.textCtrl and a wx.Log obj
     with different colors for

     Parameter:
     ----------
      parent obj
      name   : string       <"Logger">
     logLevel: wx.LOG LEVEL <wx.LOG_Error>
     listener: string       <same as name>
    """

    def __init__(self, parent, name="LOGGER", **kwargs):
        super().__init__(parent, name=name)
        self._font        = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Arial', wx.FONTENCODING_ISO8859_1)
        self._listener    = name
        self.__isInit     = False
        self.__isMinimize = False
        self._loglevel    = wx.LOG_Error
        self.update(**kwargs)

    @property
    def LogLevel(self):return self._loglevel
    @LogLevel.setter
    def LogLevel(self,l):
        self._loglevel = l
        if self.__isInit:
           self.Logger.SetLogLevel(self._loglevel)

    @property
    def PubSubListener(self):
        return self._listener

    @property
    def cmd_update_min_max(self):
        return self.PubSubListener + ".SPLIT_MIN_MAX"

    @property
    def cmd_set_status(self):
        return self.PubSubListener + ".SET_STATUS"

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, v):
        self._font = v

    @property
    def isInit(self):
        return self.__isInit
  # ---
    def _update_from_kwargs(self, **kwargs):
        self._loglevel = kwargs.get("loglevel", wx.LOG_Message)
        self._listener = kwargs.get("listener", self._listener).replace(" ", "_").upper()
        self._font     = kwargs.get("font", self._font)

  # ---
    def _init_pubsub(self, **kwargs):
        #pub.subscribe(self.SetStatus, self.cmd_set_status)
        pass

    def update(self, **kwargs):
        self._update_from_kwargs(**kwargs)
        self._wx_init()
        self._init_logger()
        self._init_pubsub(**kwargs)
        self._ApplyLayout()

    def _wx_init(self):
        self.SetBackgroundColour(wx.LIGHT_GREY)

        self._pnl = wx.Panel(self, -1)
        self._txt_head = wx.StaticText(self._pnl, wx.ID_ANY, "Logger", style=wx.ALIGN_CENTRE_HORIZONTAL)
        self._txt_head.SetBackgroundColour("grey70")

        stl = wx.BU_EXACTFIT | wx.BU_NOTEXT  # | wx.BORDER_NONE
        self._BtClear = wx.Button(self._pnl, -1, name=self.PubSubListener + ".BT.CLEAR", style=stl)
        self._BtClear.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_MENU, (12, 12)))
        self.Bind(wx.EVT_BUTTON, self.ClickOnButton, self._BtClear)

        self._BtMinimize = wx.Button(self._pnl, -1, name=self.PubSubListener + ".BT.MINIMIZE", style=stl)
        self._BtMinimize.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_MENU, (12, 12)))
        self.Bind(wx.EVT_BUTTON, self.ToggleMinimize, self._BtMinimize)

        style = wx.TE_MULTILINE | wx.TE_READONLY  # |wx.HSCROLL
        self._txtctrl = wx.TextCtrl(self, wx.ID_ANY, style=style)
        self._txtctrl.SetFont(self.font)
        self.Logger = JuMEG_wxLog(self._txtctrl)

    def _init_logger(self):
        """ """
        self.__isInit = False
        formatter=wx.LogFormatter("%(asctime)s - %(name)s - %(message)s")
        wx.Log.SetActiveTarget(self.Logger)
        wx.Log.SetFormatter(formatter)
        #wx.Log.SetTimestamp('%Y-%m-%d %H:%M:%S')
        wx.Log.SetLogLevel(self.LogLevel)
        self.__isInit = True

    def ToggleMinimize(self, evt):
        """
        toggle min/max size of logger window
        send cmd to parent splitter window via pubsub
        """
        if self.__isMinimize:
            self.__isMinimize = False
        else:
            self.__isMinimize = True
        pub.sendMessage(self.cmd_update_min_max, name=self.GetName(),
                        size=self._BtMinimize.GetSize() * 2)  # two buttons to show

    def ClickOnButton(self, evt):
        obj = evt.GetEventObject()
        if obj.GetName().startswith(self.PubSubListener + ".BT.CLEAR"):
            self._txtctrl.Clear()

    def _ApplyLayout(self):

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self._txt_head, 1, wx.ALL | wx.EXPAND, 1)
        hbox.Add(self._BtClear, 0, wx.ALL, 1)
        hbox.Add(self._BtMinimize, 0, wx.ALL, 1)
        self._pnl.SetSizer(hbox)
        self._pnl.Fit()

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self._pnl, 0, wx.ALL | wx.EXPAND, 1)
        self.Sizer.Add(self._txtctrl, 1, wx.ALL | wx.EXPAND, 1)

        self.SetSizer(self.Sizer)
        self.SetAutoLayout(1)
        self.Fit()
        self.GetParent().Layout()





# old stuff with stdout stderr

class JuMEG_LogRedirectSTD(object):
    """
    redirect some kind of STD out,err,info to a wx.Textctrl
    and write it with selected color

    Parameters
    ----------
    wx.TextCtrl obj
    color   : text/message  colour wx.Colour (r,g,b) <wx.Black>

    Hints
    ------
     https://www.blog.pythonlibrary.org/2009/01/01/wxpython-redirecting-stdout-stderr/"
     https://dzone.com/articles/python-101-redirecting-stdout
     https://www.blog.pythonlibrary.org/2014/01/31/wxpython-how-to-catch-all-exceptions/
    """
    def __init__(self,txtctrl,colour=wx.BLACK):
        self._txtctrl = txtctrl
        self._colour  = colour
        self.__isBusy = False

    @property
    def colour(self):   return self._colour
    @colour.setter
    def colour(self,v): self._colour=v

    @property
    def isBusy(self): return self.__isBusy

    def _write(self,msg):
        self.__isBusy=True
        self._txtctrl.SetDefaultStyle(wx.TextAttr(self.colour))
        self._txtctrl.AppendText(msg)
        self._txtctrl.SetDefaultStyle(wx.TextAttr(wx.NullColour))
        self._txtctrl.ShowPosition(self._txtctrl.GetLastPosition()) # scroll to end
        #self._txtctrl.SetScrollPos(wx.VERTICAL,-1)
        #self._txtctrl.SetInsertionPoint(-1)
        self._txtctrl.Refresh()
        self.__isBusy = False

    def write(self,msg):
        wx.CallAfter( self._write,msg )

    def flush(self):
        pass


class _JuMEG_wxLogger(wx.Panel):
    """
     Logger  redirect sys.stdout/-err/-in
     into a wx.TextCrtl with different colors
     work together with

    """
    def __init__(self,parent,start=True,name="LOGGER",**kwargs):
        super().__init__(parent,name=name)
        self._font = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Arial', wx.FONTENCODING_ISO8859_1)
        self.__isLogging   = False
        self.__isInit      = False
        self.__isMinimize  = False

        self._log_stdout = True
        self._log_stdin  = False
        self._log_stderr = True
        self._listener   = name

        self.update(**kwargs)

    @property
    def PubSubListener(self): return self._listener
    #@PubSubListener.setter
    #def PubSubListener(self, v): self._listener = v.replace(" ", "_").upper()

    @property
    def cmd_update_min_max(self): return self.PubSubListener + ".SPLIT_MIN_MAX"
    @property
    def cmd_set_status(self):     return self.PubSubListener + ".SET_STATUS"

    @property
    def font(selfself): return self._font
    @font.setter
    def font(self, v): self._font = v

    @property
    def isInit(self): return self.__isInit

    @property
    def isLogging(self): return self.__isLogging

    @property
    def LogStdOUT(self): return self._log_stdout
    @LogStdOUT.setter
    def LogStdOUT(self,v): self._log_stdout= v

    @property
    def LogStdIN(self): return self._log_stdin
    @LogStdIN.setter
    def LogStdIN(self, v):self._log_stdin = v

    @property
    def LogStdERR(self): return self._log_stderr
    @LogStdERR.setter
    def LogStdERR(self, v): self._log_stderr = v

   #---
    def _update_from_kwargs(self,**kwargs):
        self._listener = kwargs.get("listener", self._listener).replace(" ", "_").upper()
   #---
    def _init_pubsub(self, **kwargs):
        pub.subscribe(self.SetStatus, self.cmd_set_status)

    def update(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        self._wx_init()
        self._init_logger()
        self._init_pubsub(**kwargs)
        self.start()
        self._ApplyLayout()

    def SetStatus(self,value=True):
        if value:
           self.start()
           #self.Show()
        else:
           self.stop
           self.Hide()
            
    def start(self):
        """
        start logging
        redirect stdout/stderr/stdinfo into a wx.TextCtrl
        call with wx.CallAfter()
        """
        wx.CallAfter(self._redirect_std)

    def _stop_logging(self):
        """
        get std back not working yet
        https://dzone.com/articles/redirecting-all-kinds-stdout
        """
        self.__isLogging = False
        sys.stdout = sys.__stdout__ #self.__stdout_save
        sys.stdin  = sys.__stdin__  #self.__stdin_save
        sys.stderr = sys.__stderr__ #self.__stderr_save

    def stop(self):
        """
        stop  logging into a wx.TextCtrl
        redirect stdout/stderr/stdinfo back
        call  with wx.CallAfter()
        """
        wx.CallAfter(self._stop_logging)

    def _wx_init(self):
        self.SetBackgroundColour(wx.LIGHT_GREY)

        self._pnl = wx.Panel(self, -1)
        self._txt_head = wx.StaticText(self._pnl, wx.ID_ANY,"Logger",style=wx.ALIGN_CENTRE_HORIZONTAL )
        self._txt_head.SetBackgroundColour("grey70")

        stl = wx.BU_EXACTFIT|wx.BU_NOTEXT# | wx.BORDER_NONE
        self._BtClear = wx.Button(self._pnl,-1,name=self.PubSubListener+".BT.CLEAR",style=stl)
        self._BtClear.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_MENU,(12,12)))
        self.Bind(wx.EVT_BUTTON, self.ClickOnButton, self._BtClear)

        self._BtMinimize = wx.Button(self._pnl,-1,name=self.PubSubListener+".BT.MINIMIZE",style=stl)
        self._BtMinimize.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK, wx.ART_MENU,(12,12)))
        self.Bind(wx.EVT_BUTTON,self.ToggleMinimize,self._BtMinimize)

        style = wx.TE_MULTILINE | wx.TE_READONLY  # |wx.HSCROLL
        self._txtctrl = wx.TextCtrl(self, wx.ID_ANY, style=style)
        self._txtctrl.SetFont(self._font)

    def _init_logger(self):
        """ """
        self.__isLogging = False
        self.__isInit    = False
        self._stdout = JuMEG_LogRedirectSTD(self._txtctrl,colour=wx.BLACK)
        self._stdin  = JuMEG_LogRedirectSTD(self._txtctrl,colour=wx.GREEN)
        self._stderr = JuMEG_LogRedirectSTD(self._txtctrl,colour=wx.RED)
        self.__isInit = True

    def _redirect_std(self):
        """ """
        if self.isLogging : return
        if not self.isInit: self._init_logger()

        try:
           self.__stdout_save = sys.stdout
           self.__stdin_save  = sys.stdin
           self.__stderr_save = sys.stderr

           if self.LogStdOUT:
              sys.stdout = self._stdout
           if self.LogStdIN:
              sys.stdin  = self._stdin
           if self.LogStdERR:
              sys.stderr = self._stderr

        except Exception as e:
            print(e)

        self.__isLogging = True

    def ToggleMinimize(self,evt):
        """
        toggle min/max size of logger window
        send cmd to parent splitter window via pubsub
        """
        if self.__isMinimize:
           self.__isMinimize = False
        else:
           self.__isMinimize = True
        pub.sendMessage(self.cmd_update_min_max,name=self.GetName(),size=self._BtMinimize.GetSize()*2) # two buttons to show

    def ClickOnButton(self,evt):
        obj = evt.GetEventObject()
        if obj.GetName().startswith(self.PubSubListener+".BT.CLEAR"):
           self._txtctrl.Clear()

    def _ApplyLayout(self):
       # Add widgets to a sizer

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self._txt_head,1,wx.ALL | wx.EXPAND, 1)
        hbox.Add(self._BtClear,0,wx.ALL, 1)
        hbox.Add(self._BtMinimize,0,wx.ALL, 1)
        self._pnl.SetSizer(hbox)
        self._pnl.Fit()

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self._pnl, 0, wx.ALL | wx.EXPAND, 1)
        self.Sizer.Add(self._txtctrl, 1, wx.ALL | wx.EXPAND, 1)

        self.SetSizer(self.Sizer)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()
