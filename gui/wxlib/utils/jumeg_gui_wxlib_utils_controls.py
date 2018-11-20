#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 27 22:35:34 2017

@author: fboers
"""

import wx
from wx.lib.pubsub import pub

#try:
#    from agw import floatspin as FS
#except ImportError: # if it's not there locally, try the wxPython lib.

import wx.lib.agw.floatspin as FS

__version__='2018-08-22-001'


class JuMEG_wxSplitterWindow(wx.SplitterWindow):
    def __init__(self, parent,**kwargs):
        """
        JuMEG wx.SplitterWindow with method to shrink and

        Parameters
        ----------
         parent        : wx.Widged
         listener      : name of pubsub listener to subscribe <SPLITTER>
         flip_position : key word for pubsub listener to flip position <FLIP_POSITION>
         split_min_max : key word for pubsub listener to reise windows <SPLIT_MIN_MAX>

         pubsub calls:
          <listener>.<flip_position> : change window position left7/right or up/down
          <listener>.<split_min_max> : rezise shrink/enlarge one window

        """
        super(JuMEG_wxSplitterWindow,self).__init__(parent=parent, id=wx.ID_ANY,style=wx.SP_3DSASH|wx.SP_3DBORDER|wx.SUNKEN_BORDER)
        self._listener      = "SPLITTER"
        self._flip_position = "FLIP_POSITION"
        self._split_min_max = "SPLIT_MIN_MAX"
        self.__split_factor_list  = [-1.0,0.5,1.0]
        self.__split_position_idx = 1
        self.SetSashGravity(1.0) # expamd top/left
        self.SetMinimumPaneSize(100)
        self.update(**kwargs)

    @property
    def PubSubListener(self): return self._listener

    @property
    def PubSubListenerFlipPosition(self): return self.PubSubListener+"."+self._flip_position
    @property
    def PubSubListenerSplitMinMax(self):  return self.PubSubListener+"."+self._split_min_max

   #---
    def _update_from_kwargs(self,**kwargs):
        self._listener     = kwargs.get("listener", self._listener).replace(" ", "_").upper()
        self._flip_position= kwargs.get("flip_position", self._flip_position).replace(" ", "_").upper()
        self._split_min_max= kwargs.get("split_min_max", self._split_min_max).replace(" ", "_").upper()
   #---
    def _init_pubsub(self,**kwargs):
        pub.subscribe(self.FlipPosition,self.PubSubListenerFlipPosition)
        pub.subscribe(self.UpdateSplitPosition,self.PubSubListenerSplitMinMax) # "SPLITTER.SPLIT_MIN_MAX"
        #print("SPLITTER MIN MAX: "+self.PubSubListenerSplitMinMax)

    def update(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        self._init_pubsub(**kwargs)
        self._PanelA = None
        self._PanelB = None
        self.__v     = None
        self.__h     = None

    def UpdateSplitPosition(self,name=None,size=None):
        """
        update split position change window size to min,50%,max
        Parameter
        ---------
         name : name of the window eg: name of window 1 or 2 <None>
         size: wx.GetSize() to set MinimumPaneSize <None>
        """
        if not size: return
        if name not in [self.GetWindow1().GetName(), self.GetWindow2().GetName()]: return

        max_pos = 0

        if self.GetSplitMode() == wx.SPLIT_VERTICAL:
           pos     = size[0]
           max_pos = self.GetSize()[0]
        else:
           pos = size[1]
           max_pos = self.GetSize()[1]
        self.SetMinimumPaneSize(abs(pos) + 2)

        idx = self.__split_factor_list[self.__split_position_idx]
        self.__split_position_idx+=1
        self.__split_position_idx = self.__split_position_idx % len(self.__split_factor_list)

        if idx == -1:
           self.SetSashPosition(max_pos, redraw=True)
        elif idx == 0.5:
           self.SetSashPosition(max_pos * 0.5,redraw=True)
        else:
           self.SetSashPosition(1,redraw=True)

    def FlipPosition(self,value=wx.SPLIT_VERTICAL):
        """
        flips panels inside splitter

        Parameter
        ---------
        value: vertical,horizontal <vertical>
        """
        #--- todo check  keep sahposition
        # wx.SplitterWindow.GetSplitMode
        #spos = self.GetSize()[-1] - self.GetSashPosition()

        if not value: return
        w1 = self.GetWindow1()
        w2 = self.GetWindow2()
        self.Unsplit()

       # --- flip windows
        if w1 and w2:
           if not self.__v:
                  self.__v = [w1, w2]
           if value == wx.SPLIT_VERTICAL:
              if self.GetSplitMode() == wx.SPLIT_VERTICAL:
                  self.__v.reverse()
              self.SplitVertically(window1=self.__v[0], window2=self.__v[1],sashPosition=self.__v[0].GetSize()[-1] * 0.5)
           else:
              if self.GetSplitMode() == wx.SPLIT_HORIZONTAL:
                 self.__v.reverse()
              self.SplitHorizontally(window1=self.__v[0],window2=self.__v[1],sashPosition=self.__v[0].GetSize()[0] * 0.5)

           self.SetSashGravity(1.0)
           self.Fit()
           self.GetParent().Layout()


class JuMEG_wxCMDButtons(wx.Panel):
      ''' panel with Close,Cancel,Apply Buttons '''

      def __init__(self, parent,**kwargs):
          super(JuMEG_wxCMDButtons,self).__init__(parent=parent, id=wx.ID_ANY,style=wx.SUNKEN_BORDER)
          self._init(**kwargs)

      @property
      def CallClickOnApply(self):
          return self.prefix.upper() + ".BT_APPLY".upper()
      @property
      def CallClickOnCancel(self):
          return self.prefix.upper() + ".BT_CANCEL".upper()

      def SetVerbose(self,value=False):
          self.verbose = value

      def update_from_kwargs(self,**kwargs):
          self.verbose = kwargs.get("verbose", False)
          self.debug   = kwargs.get("debug", False)
          self.prefix  = kwargs.get("prefix","CMD_BUTTONS")

      def init_pubsub(self):
        """"
        init pubsub call
        """
        pub.subscribe(self.SetVerbose,'MAIN_FRAME.VERBOSE')

      def wx_init(self,**kwargs):
          """ init WX controls """
          #self.SetBackgroundColour(wx.Colour([200,200,200] ))
        #--- BTs
          ctrls = []
          ctrls.append(["CLOSE" ,"BT_CLOSE", wx.ALIGN_LEFT,"Close program",  self.ClickOnCTRL])
          ctrls.append(["CANCEL","BT_CANCEL",wx.ALIGN_LEFT,"Cancel progress",self.ClickOnCTRL])
          ctrls.append(["APPLY","BT_APPLY",wx.ALIGN_RIGHT,"Apply command",self.ClickOnCTRL])
          self._PNL_BTN = JuMEG_wxControlButtonPanel(self,label=None,control_list=ctrls)
          self.SetBackgroundColour( wx.Colour([230,230,230]) )
          self._PNL_BTN.SetBackgroundColour(wx.Colour([180,200,200]))

      def update(self, **kwargs):
          pass

      def _init(self,**kwargs):
          """" init """
          self.update_from_kwargs(**kwargs)
          self.wx_init()
          self.init_pubsub()
          self.update(**kwargs)
          self._ApplyLayout()

      def ClickOnCTRL(self,evt):
          obj=evt.GetEventObject()
          if obj.GetName().upper().startswith("BT_CLOSE"):
             pub.sendMessage("MAIN_FRAME.CLICK_ON_CLOSE",evt=evt)
          elif not obj.GetName().upper().startswith("WXSPINCTRL"):
             #print("JuMEG_wxCMDButtons.ClickOnCTRL: ")
             print("  --> PubSub Call: "+ self.prefix.upper() + "." + obj.GetName().upper())
             pub.sendMessage(self.prefix.upper() + "." + obj.GetName().upper())

      def _ApplyLayout(self):
          """" default Layout Framework """
          ds=1
          self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
          #self.Sizer.Add((0,0), 1, wx.ALIGN_LEFT | wx.EXPAND | wx.ALL, ds)
          self.Sizer.Add(self._PNL_BTN, 1, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL, ds)
          self.SetSizer(self.Sizer)
          self.Fit()
          self.SetAutoLayout(1)
          self.GetParent().Layout()


class _JuMEG_wxControlButtons_Old(wx.Panel):
    def __init__(self, parent,boxsizer=wx.HORIZONTAL):
        """"""
        super(JuMEG_wxControlButtons,self).__init__(parent=parent, id=wx.ID_ANY,style=wx.SUNKEN_BORDER)
        
        self.label    = 'Buttons'
        self.boxsizer = boxsizer       
        self.SetBackgroundColour('white')
        
        self.BtApply= wx.Button(self,id=wx.ID_APPLY,label='Apply')
        self.BtApply.Bind(wx.EVT_BUTTON, self.ClickOnBtApply)
        
        self.BtExit         = wx.Button(self,id=wx.ID_EXIT)
        self.BtCloseDisplay = wx.Button(self,id=wx.ID_ANY,label='CloseDisplay')
        self.BtInitDisplay  = wx.Button(self,id=wx.ID_ANY,label='InitDisplay')
        
        self.__btlist2disable=[self.BtExit,self.BtCloseDisplay,self.BtInitDisplay]
    
        self.__ApplyLayout()
        
    def ClickOnBtApply(self,evt):
        if evt:
           #self.BtApply.GetId() == wx.ID_APPLY
           self.BtApply.SetId(wx.ID_STOP)
           self.BtApply.SetLabel('Stop')
           evt.Skip()
        else:
           self.BtApply.SetId(wx.ID_APPLY)
           self.BtApply.SetLabel('Apply')
    
    def SetButtonState(self,state):
        for bt in self.__btlist2disable:
           if state:
              bt.Enable()
           else:
              bt.Disable()
    
    def __ApplyLayout(self):
        self.Sizer = wx.BoxSizer(self.boxsizer)
        self.Sizer.Add(self.BtApply,1, wx.ALIGN_LEFT|wx.ALL, 5)
        self.Size.Add(self.BtInitDisplay,1,wx.ALIGN_LEFT|wx.ALL, 5)
        self.Size.Add(self.BtCloseDisplay,1,wx.ALIGN_LEFT|wx.ALL, 5)
        self.Size.Add((0,0),1,wx.ALIGN_LEFT|wx.EXPAND|wx.ALL, 5)
        self.Sizer.Add(self.BtExit,1,wx.ALIGN_RIGHT|wx.ALL, 5)
          
        self.SetSizer(self.Sizer)

class JuMEG_wxControlButtons(object):
    def __init__(self, parent,prefix="CONTROL_BUTON",AddGrowableCol=None,list=None,init=True):
        """ wx.Button in a panel """
        super(JuMEG_wxControlButtons,self).__init__() #parent=parent, id=wx.ID_ANY,style=wx.SUNKEN_BORDER)
        self._parent        = parent
        self.prefix         = prefix
        self.AddGrowableCol = AddGrowableCol
        self._isInit        = False
        self.label          = None
        self._control_panel = None

        if list:
           self._wxctrl_list = list
        else:
            self.init_wxcltr_list()
        if init:
           self._init_control_panel()

    @property
    def ControlPanel(self):
        if not self._isInit:
           self._init_control_panel()
        return self._control_panel

    def _init_control_panel(self):
        self._control_panel = JuMEG_wxControlButtonPanel(self._parent,label=self.label,control_list=self._wxctrl_list,AddGrowableCol=self.AddGrowableCol)
        self._isInit = True

    def init_wxcltr_list(self):
        self._wxctrl_list =[]
        self._wxctrl_list.append(["CLOSE","Close",wx.ALIGN_LEFT,"Close program",self.ClickOnButon])
        self._wxctrl_list.append(["CANCEL","Cancel",wx.ALIGN_LEFT,"Cancel progress",self.ClickOnButon])
        self._wxctrl_list.append([None,None,wx.ALIGN_LEFT|wx.EXPAND,None,None])
        self._wxctrl_list.append(["APPLY","Apply",wx.ALIGN_RIGHT,"Apply command",self.ClickOnButon])

    def ClickOnButon(self,evt):
        obj=evt.GetEventObject()
        # print("JuMEG_wxControlButtons CTL Button: {}".format(self.prefix +"."+ obj.GetName().upper()))
        pub.sendMessage(self.prefix +"."+ obj.GetName().upper() )

class JuMEG_wxControlUtils(object):
    def __init__(self, parent):
        super (JuMEG_wxControlUtils,self).__init__()
    # ---
    def get_button_txtctrl(self, obj):
        """ finds the textctr related to the button event
        Parameters:
        -----------
        wx control button

        Results:
        ---------
        wx textctrl obj

        """
        return self.FindWindowByName(obj.GetName().replace("BT_", ""))

    # ---
    def FindControlByObjName(self, obj, prefix="", seperator="_"):
        """
        finds a obj ctrl by an other object and prefix to change

        Parameters:
        -----------
        obj to get the name from
        prefix: string to replace the input obj.Name startswith <"">

        Results:
        ---------
        wx ctrl obj

        Example:
        --------
        input obj with name: BT_PATH
        prefix: "COMBO"
        return ComboBox obj with name "COMBO_PATH"

        FindControlByObjName(obj_bt,"COMBO")

        """
        s = obj.GetName().split(seperator)[0]
        return self.FindWindowByName(obj.GetName().replace(s, prefix, 1))

   # ---
    def UpdateComBox(self, cb, vlist, sort=True):
        """
        update wx.ComboBox: clear,SetItems,SetValue first element in list
        remove double items and sort list

        Parameters:
        -----------
        combobox obj
        list to insert
        sort : will sort list <True>
        """
        # if not cb: return
        cb.Enable(False)
        cb.Clear()
        if vlist:
            if isinstance(vlist, (list)):
                # avoid repetitios in list, make list from set
                if sort:
                    cb.SetItems(sorted(list(set(vlist))))
                else:
                    cb.SetItems(list(set(vlist)))
            else:
                cb.SetItems([vlist])
            cb.SetSelection(0)
            cb.SetValue(vlist[0])
        else:
            cb.Append('')
            cb.SetValue('')
            cb.Update()
        cb.Enable(True)

class JuMEG_wxControlBase(wx.Panel,JuMEG_wxControlUtils):
    """
    generate button, text,spin/floatspin combobox controls
     
    Parameters:
    ---------- 
     parent widged
     control_list: list of parameter and definition for widged controls
     label       : headline text
     drawline    : draw a line on top as separator <True>
     bg          : background color <"grey90">
     boxsizer    : [wx.VERTICAL,wx.HORIZONTAL] <wx.VERTICAL>
     
     FlexGridSizer parameter:
      AddGrowableCol : int or list    <None> 
      AddGrowableRow : int or list    <None>
      -> col[i] or row[i] will grow/expand  use full to display long textfields
      
      cols           : number of cols in FGS <4>, may will be ignored due to task  
      rows           : number of rows in FGS <1>, may will be ignored due to task
     
        
     Results:
     --------
     wx.Panel with sub controls group by wx.FlexGridSizer    

     Example:   
     --------
       Button  : ( control type,name,label,help,callback) 
                 ("BT","START","Start","press start to start",ClickOnButtton)
       
       CheckBox: ( control type,name,label,value,help.callback) 
                 ("CB","VERBOSE","verbose",True,'tell me more',ClickOnCheckBox)
       
       ComboBox: ( control type,name,value,choices,help,callback) 
                 ("COMBO","COLOR","red",['red','green'],'select a color',ClickOnComboBox)
        
       TxtCtrl : ( control type,name,label,help,callback) 
                 ("TXT","INFO","info","read carefully",ClickOnTxt)
       
       StaticText : ( control type,name,label,help,callback) 
                 ("STXT","INFO","info","read carefully",NoneClickOnTxt)
      
           
       SpinCtrl     : ( control type,label,[min,max,increment],value,help,callback) 
                      ("SP","Xpos",[-500,500,10],11,"change x position",ClickOnSpin)
                 
       FloatSpinCtrl: ( control type,label,[min,max,increment],value,help,callback) 
                      ("SPF","Xpos",[-500.0,500.0,10.0],11,"change x position",ClickOnFloatSpin)
                      
      
     in sub class __init__ call to add controls 
     self.add_controls(vbox)  
     
    """
    def __init__(self, parent,control_list=None,label='TEST',drawline=True,bg="grey90",boxsizer=wx.VERTICAL,AddGrowableCol=None,AddGrowableRow=None,cols=4,rows=1):
        super (JuMEG_wxControlBase,self).__init__(parent,id=wx.ID_ANY,style=wx.SUNKEN_BORDER)
        self.box = wx.BoxSizer(boxsizer)
        self.SetBackgroundColour(bg)
       
        self._obj   = None   
        self._rows  = rows
        self._cols  = cols
        self.label  = label
        self.drawline = drawline
        
        self.gap   = 4
        self.gap_minmax = 1
        self.vgap  = 4
        self.hgap  = 4
        self.LE    = wx.LEFT |wx.EXPAND
        self.RE    = wx.RIGHT|wx.EXPAND
        self.GS    = None
        
        self.list_of_controls = control_list
        self.AddGrowableCol   = AddGrowableCol
        self.AddGrowableRow   = AddGrowableRow
        
        self.boxsizer = wx.BoxSizer(boxsizer)
        
        self.SetBackgroundColour(bg)

       #--- in sub class call to add controls 
       # vbox = self.add_controls(vbox) 
             
    @property
    def cols(self): return self._cols
    @cols.setter
    def cols(self,v): self._cols=v
    
    @property
    def rows(self): return self._rows
    @rows.setter
    def rows(self,v): self._rows=v
     
    @property
    def controls(self): return self._obj
    @property
    def objects(self) : return self._obj

    def init_growable(self):
        """ expand / grow col row """
        if self.AddGrowableCol:
           if isinstance(self.AddGrowableCol,(list,tuple)):
              for c in self.AddGrowableCol:
                  if c < self.cols: self.GS.AddGrowableCol(c)
           else:
              if self.AddGrowableCol < self.cols: self.GS.AddGrowableCol(self.AddGrowableCol)

       #--- epand / grow row
        if self.AddGrowableRow:
           if isinstance(self.AddGrowableRow,(list,tuple)):
              for r in self.AddGrowableRow:
                  if r < self.rows:
                     self.FSG.AddGrowableRow(r)
           else:
              if self.AddGrowableRow < self.rows: self.GS.AddGrowableRow(self.AddGrowableRow)

    def gs_add_empty_cell(self):
        """ adds  empty cell / space """
        self.GS.Add( (0,0),0,self.LE,self.gap)          
     
    def _gs_add_add_first_text_info(self,d):
        """ add text in front of control """
        if d[1]:
           self.GS.Add( wx.StaticText(self,-1,label=d[1],style=wx.ALIGN_LEFT),0,wx.LEFT,self.gap) 
   
    def _gs_add_add_last_obj(self):
        """ helper fct: add last obj to add """
        self.GS.Add(self._obj[-1],0,self.LE,self.gap)        
    
    def _gs_add_init_last_obj(self,d,evt=None):
        """ helper fct: init last obj to add """
        self._obj[-1].SetName(d[1])
        
        if isinstance(d[-2],str):
           self._obj[-1].SetToolTip(wx.ToolTip(d[-2]))
        if evt:
           if callable(d[-1]) : self._obj[-1].Bind(evt,d[-1])
        self._gs_add_add_last_obj()
    
    def _gs_add_Button(self,d):
        """ add Button"""
        self._obj.append(wx.Button(self,wx.NewId(),label=d[2],style=wx.BU_EXACTFIT))
        self._gs_add_init_last_obj(d,evt=wx.EVT_BUTTON)

    def _gs_add_FlatButton(self,d):
        """ add FlatButton"""
        self._obj.append(wx.Button(self,wx.NewId(),label=d[2],style=wx.BU_EXACTFIT|wx.NO_BORDER))
        self._gs_add_init_last_obj(d,evt=wx.EVT_BUTTON)

    def _gs_add_CheckBox(self,d):
        """ add wx.CheckBox"""
        self._obj.append( wx.CheckBox(self,wx.NewId(),label=d[2] ) )  
        self._obj[-1].SetValue(d[3])
        self._gs_add_init_last_obj(d,evt=wx.EVT_CHECKBOX)             
        
    def _gs_add_ComboBox(self,d):
        """ add wx.ComboBox """
        self._obj.append(wx.ComboBox(self,wx.NewId(),choices=d[3],style=wx.CB_READONLY))
        self._obj[-1].SetValue(d[2])
        self._gs_add_init_last_obj(d,evt=wx.EVT_COMBOBOX)
        
    def _gs_add_TextCtrl(self,d):
        """ add wx.TextCrtl """
        self._obj.append( wx.TextCtrl(self,wx.NewId() ))   
        self._obj[-1].SetValue(d[2])
        self._gs_add_init_last_obj(d,evt=wx.EVT_TEXT)
            
    def _gs_add_StaticText(self,d):
        """ add wx.StaticText """
        self._obj.append(wx.StaticText(self,wx.NewId(),style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_MIDDLE))
        self._obj[-1].SetLabel(d[2])
        self._gs_add_init_last_obj(d)
        
    def _gs_add_min_max_button(self,l,n):  
        """ add button MIN or MAX set to min or max in range of SpinCtrl"""
        self._obj.append( wx.Button(self,wx.NewId(),label=l,style=wx.BU_EXACTFIT,name=n) )
        self._obj[-1].Bind(wx.EVT_BUTTON,self.OnClickMinMax)
        self.GS.Add(self._obj[-1],0,wx.LEFT,self.gap_minmax)
            
    def _gs_add_SpinCtrl(self,d):
        """ add wx.SpinCtrl """
        self._obj.append( wx.SpinCtrl(self,wx.NewId(),style=wx.SP_ARROW_KEYS|wx.SP_WRAP|wx.TE_PROCESS_ENTER|wx.ALIGN_RIGHT))
        self._obj[-1].SetLabel(d[1])
        self._obj[-1].SetName("SP_"+d[1].upper())
        self._obj[-1].SetToolTip("Min: " + str(d[2][0]) +"  Max: " + str(d[2][1]) )
        self._obj[-1].SetRange(d[2][0],d[2][1])
        self._obj[-1].SetValue(d[3])
        self._obj[-1].Bind(wx.EVT_SPINCTRL, d[-1])  #5

       #self.GS.Add(self._obj[-1],0,wx.LEFT|wx.EXPAND,self.gap)
        self.GS.Add(self._obj[-1],0,wx.LEFT,self.gap)

    def _gs_add_FloatSpin(self,d):
        """ add wx.FloatSpin """
        self._obj.append( FS.FloatSpin(self,wx.NewId(),min_val=d[2][0],max_val=d[2][1],increment=d[2][2],value=1.0,agwStyle=FS.FS_RIGHT) )   
        self._obj[-1].SetLabel(d[1])
        self._obj[-1].SetName("FSP_"+d[1].upper())
        self._obj[-1].SetFormat("%f")
        self._obj[-1].SetDigits(3)
        self._obj[-1].SetValue(d[3])
        self._obj[-1].Bind(wx.EVT_SPINCTRL, d[-1])  #6 
        #self.GS.Add(self._obj[-1],0,wx.LEFT|wx.EXPAND,self.gap)
        self.GS.Add(self._obj[-1],0,wx.LEFT,self.gap)

    def add_controls(self):
       #--- Label + line 
        gap=1
        self.Sizer = wx.BoxSizer(wx.VERTICAL)

        if self.drawline:
           gap=15
           self.Sizer.Add( wx.StaticLine(self),0, wx.EXPAND|wx.ALL,5 )
        if self.label:
           gap=15
           self.Sizer.Add( wx.StaticText(self,0,label=self.label),0,wx.LEFT,5)

        self.Sizer.Add( self.initControl(),0,wx.EXPAND|wx.ALL,gap)
        
        self.SetSizer(self.Sizer)   
        self.SetAutoLayout(1)
        
        return self
   
    def init_number_of_rows_cols(self):
        """ cal number of rows  and cols
        
        Results:
        ----------
        number of rows and cols
        """
              
        if self.boxsizer.Orientation == wx.VERTICAL:
           self.rows = len( self.list_of_controls )
        else: # horizontal 
           self.cols = self._cols * len(self.list_of_controls)
            
        return self.rows,self.cols 
    
    def init_GridSizer(self):
        """ init wx.FelxGridSizer """
        
        self.init_number_of_rows_cols()
        
        self.GS = wx.FlexGridSizer(self.rows,self.cols,self.vgap,self.hgap)

        self.init_growable()
  
    def initControl(self):
        """generate and pack wx controls into a wx.FlexGridSizer
        
        Results:
        ---------
         wx.FlexGridSizer with controls
         
        """
        self._obj=[]
        self.init_GridSizer()           
          
        for d in self.list_of_controls:
            
            self._gs_add_add_first_text_info(d)
           
           #--- Button
            if   d[0] == "BT"   : self._gs_add_Button(d)
           #--- FlatButton
            elif d[0] == "FLBT" : self._gs_add_FlatButton(d)
           #--- CheckButton
            elif d[0] == 'CK'   : self._gs_add_CheckBox(d)  
           #---ComboBox      
            elif d[0] == "COMBO": self._gs_add_ComboBox(d)
           #---wx.TextCtrl     
            elif d[0] == 'TXT'  : self._gs_add_TextCtrl(d)
           #---wx.StaticText     
            elif d[0] == 'STXT' : self._gs_add_StaticText(d)
           #---  MIN/MAXSpin Buttons
            elif d[0].startswith('SP'):
           #--- min button 
                 self._gs_add_min_max_button("|<","MIN")
           #---SpinCrtl     
                 if d[0] == 'SP'   : self._gs_add_SpinCtrl(d)
           #---FloatSpinCrtl      
                 elif d[0] == "SPF": self._gs_add_FloatSpin(d)
           #--- max button   
                 self._gs_add_min_max_button(">|","MAX")
           
            else:
               self.gs_add_empty_cell()
               #self.GS.Add(wx.StaticText(self,-1,label="NOT A CONTROLL"),wx.EXPAND,self.gap)
               #self.gs_add_empty_cell()
                
        return self.GS                    

    def OnClickMinMax(self,evt): 
        obj = evt.GetEventObject()
          
    #--- get obj SpinCtrl   
        if   obj.GetName() == "MIN":
             obj_sp = self.FindWindowById( obj.GetId()+1)
             obj_sp.SetValue( obj_sp.GetMin() )
        elif obj.GetName() == "MAX": 
             obj_sp = self.FindWindowById( obj.GetId()-1)
             obj_sp.SetValue( obj_sp.GetMax() )
        else:
            evt.Skip()
            return    
        evtsp = wx.CommandEvent(wx.EVT_SPINCTRL.typeId, obj_sp.GetId()) 
        evtsp.SetEventObject(obj_sp)
        obj_sp.ProcessEvent(evtsp)   
    
      
class JuMEG_wxControls(JuMEG_wxControlBase):
    """
    generate button, text,spin/floatspin combobox controls
     
    Parameters:
    ---------- 
     parent widged
     control_list: list of parameter and definition for widged controls
     label       : headline text
     bg          : background color <"grey90">
     boxsizer    : [wx.VERTICAL,wx.HORIZONTAL] <wx.VERTICAL>
        
     FlexGridSizer parameter
      AddGrowableCol : int or list    <None> 
      AddGrowableRow : int or list    <None>
      -> col[i] or row[i] will grow/expand  use full to display long textfields
      
     Results:
     --------
     wx.Panel with sub controls group by wx.FlexGridSizer    

     Example:
     --------
       control_list: array of( ( type,label,min,max,value,callback fct) )
        control_list = ( ("SP","Xpos",-500,500,0,self.OnSpinXYpos),
                         ("SP","Ypos",-500,500,0,self.OnSpinXYpos),
                         ("SP","Width",1,5000,640,self.OnSpinSize),
                         ("SP","Height",1,5000,480,self.OnSpinSize)
                        )   
        
        
    """
    def __init__(self,parent,**kwargs):
        super(JuMEG_wxControls, self).__init__(parent,**kwargs) 
        
       #--- add controls 
        self.add_controls() 
             
    def _gs_add_add_last_obj(self):
        """ helper fct: add last obj to add """
        self.gs_add_empty_cell()
        self.GS.Add(self._obj[-1],0,self.LE,self.gap)
        self.gs_add_empty_cell()
        
    
class JuMEG_wxControlGrid(JuMEG_wxControlBase):
    """
     generate controls in a grid e.g. for CheckButton
     
     Parameters:
     -----------    
      title   : text
      bg      : background colo
      boxsizer: sizer  [<wx.VERTICAL>,wx.HORIZONTAL]
      control_list :

     Results:
     --------
     wx.Panel with sub controls group by wx.FlexGridSizer    


    """
    def __init__(self,parent,**kwargs):
       super(JuMEG_wxControlGrid,self).__init__(parent,**kwargs)
       
      #--- add controls 
       self.add_controls() 
    
    
    def _gs_add_add_first_text_info(self,d):
        """ add text in front of control """
        pass
         
    def init_number_of_rows_cols(self):
        """ cal number of rows  and cols
        
        Results:
        ----------
        number of rows and cols
        """
        if self.cols == 1:
           self.rows = len( self.list_of_controls )
        else:
           self.rows,rest = divmod( len( self.list_of_controls ),self.cols)
           if rest:
              self.rows += 1

        return self.rows,self.cols

class JuMEG_wxControlIoDLGButtons(JuMEG_wxControlBase):
    """
    generate Buttons and TextCtrl to show File/Dir dialog and display filename or path in textfield
   
    """
    def __init__(self, parent,**kwargs):
        super (JuMEG_wxControlIoDLGButtons,self).__init__(parent,**kwargs)
      #--- add controls 
        self.cols = 2
        self.add_controls() 
    
    def _gs_add_add_first_text_info(self,d):
        """ add text in front of control """
        pass    
    
    def init_number_of_rows_cols(self):
        """ cal number of rows  and cols
        
        Results:
        ----------
        number of rows and cols
        """
       
        self.rows = len( self.list_of_controls )
        return self.rows,self.cols 

class JuMEG_wxControlButtonPanel(JuMEG_wxControlBase):
    """
     generate controls in a grid e.g. for CheckButton
     
     Parameters:
     -----------    
      title   : text
      bg      : background colo
      boxsizer: sizer  [<wx.VERTICAL>,wx.HORIZONTAL]
      control_list :
     
     Results:
     --------
     wx.Panel with sub controls group by wx.FlexGridSizer    
     
     Example:   
     --------
       Button  : (label,name,pack option,wx-event,help,callback) 
                 (["CLOSE","Close",wx.ALIGN_LEFT,"Close program",self.ClickOnButton ],
                  ["CANCEL","Cancel",wx.ALIGN_LEFT,"Cancel progress",self.ClickOnButton],
                  ["APPLY","Apply",wx.ALIGN_RIGHT,"Apply command",self.ClickOnButton])
              
    """
    def __init__(self,parent,**kwargs):
       super(JuMEG_wxControlButtonPanel,self).__init__(parent,**kwargs)
       self.gap   = 3
       self.vgap  = 5
       self.hgap  = 4
       self.RE    = wx.RIGHT|wx.EXPAND
       self.SetBackgroundColour("grey40")      

      #--- add controls 
       self.add_controls() 
    
    def add_controls(self):
       #--- Label + line 
        sbox = wx.BoxSizer(wx.VERTICAL)
        if self.label:
           sbox.Add( wx.StaticText(self,0,label=self.label),0,wx.LEFT,2)
           sbox.Add( wx.StaticLine(self),0, wx.EXPAND|wx.ALL,1 ) 
           
        sbox.Add( self.initControl(),0,wx.EXPAND|wx.ALL|wx.ALIGN_CENTER,self.hgap )
        self.SetAutoLayout(True)
        self.SetSizer(sbox)   
        
        return sbox
    
    def _gs_add_add_last_obj(self,d):
        """ helper fct: add last obj to add """
        if d[2] & (wx.ALIGN_RIGHT|wx.EXPAND):
           self.GS.AddStretchSpacer(prop=1)
        self.GS.Add(self._obj[-1],0,d[2]|wx.ALL,self.gap)
            
    def _gs_add_init_last_obj(self,d,evt=None):
        """ helper fct: init last obj to add """
        self._obj[-1].SetName(d[1])
        
        if isinstance(d[-2],str):
           self._obj[-1].SetToolTip(wx.ToolTip(d[-2]))
        if evt:
           if callable(d[-1]) : self._obj[-1].Bind(evt,d[-1])
        self._gs_add_add_last_obj(d)   
        
    def _gs_add_Button(self,d):
        """ add Button"""
        if d[0]:
           self._obj.append(wx.Button(self,wx.NewId(),label=d[0]))
           self._gs_add_init_last_obj(d,evt=wx.EVT_BUTTON)
        else: # add separator
           self.GS.Add(0,0,d[2]|wx.ALL,self.gap)

    def init_GridSizer(self):
        """ 
        
        Results:
        --------
        wx.GridSizer
        """
        self.GS = wx.BoxSizer(wx.HORIZONTAL)

    def initControl(self):
        """generate and pack wx controls into a wx.FlexGridSizer
        
        Results:
        ---------
         wx.FlexGridSizer with controls
         
        """
        self._obj=[]
        self.init_GridSizer() 
        
        for d in self.list_of_controls:
            self._gs_add_Button(d)
      
        return self.GS

