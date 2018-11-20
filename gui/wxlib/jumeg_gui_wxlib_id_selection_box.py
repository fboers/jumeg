#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 15:28:58 2018

@author: fboers
"""
import wx
import wx.lib.masked as masked
from wx.lib.pubsub import pub
from jumeg.template.jumeg_template       import JuMEG_Template_Experiments
from jumeg.gui.utils.jumeg_gui_utils_io  import JuMEG_UtilsIO_Id


__version__='2018-03-27.001'

class JuMEG_wxIdSelectionBox(wx.Panel):
    """
     JuMEG_wxSelectionBox
      input 
         parent widged 
           stage  : stage path to experiment e.g. /data/XYZ/exp/M100
           pubsub : false; use wx.pubsub msg systen sends like:
                    pub.sendMessage('EXPERIMENT_TEMPLATE',stage=stage,experiment=experiment,TMP=template_data)
           or button event <ID_SELECTION_BOX_UPDATE> from Update button
           id_mask: #######; mask for id selection
           verbose: False
           bg     : grey90 backgroundcolor
    """
    def __init__(self,parent,title='ID',stage=None,bg="grey90",name="ID_SELECTION_BOX",pubsub=True,id_mask='#######',*kargs, **kwargs):
        super(JuMEG_wxIdSelectionBox, self).__init__(parent,name=name)
        self.pubsub  = pubsub
        self.id_mask = id_mask
        self.ID      = JuMEG_UtilsIO_Id()
        self.stage   = stage
        
        self._item_list          = []
        self._item_selected_list = []
        self._title              = title
        
        self.SetBackgroundColour(bg)
        self._wx_init()
      
        self._ApplyLayout()
    
    def _wx_init(self,bg='grey80'):
        
        self._wxTxtIdInfo = wx.StaticText(self, 0,label="000 / 000")
       #--- de/select toggle bt  
        self._wxBtSelect  = wx.Button(self, -1, name=self.GetName().upper()+".ID_SELECT",label='SELECT')
        self._wxBtSelect.Bind(wx.EVT_BUTTON, self.ClickOnButton)
       #--- id mask       
        self._wxMaskId = masked.TextCtrl(self,-1,'', mask = self.id_mask)  
       #--- id listbox  
        self._LB      = wx.ListBox(self,-1,style=wx.LB_MULTIPLE|wx.BORDER_SUNKEN)
        self._LB.Bind( wx.EVT_LISTBOX,self.ClickOnDeSelect)      
       #--- Update Bt
        self._wxBtUpdate  = wx.Button(self, -1, name=self.GetName().upper()+".UPDATE",label="Update")
        self._wxBtUpdate.Bind(wx.EVT_BUTTON,self.ClickOnButton)       
    
    def __get_stage(self):
        return self.ID.stage
    def __set_stage(self,v):
        self.ID.stage=v
    stage = property(__get_stage,__set_stage)
   
    def ClickOnButton(self,evt):
        obj = evt.GetEventObject()
     #--- de/select bt
        if obj.GetName().endswith('ID_SELECT'):
          #--- deselect all first 
           for i in range(self._LB.GetCount()):
               self._LB.Deselect(i)
           if obj.GetLabel().startswith('DE'):
              obj.SetLabel('SELECT') 
           else:
              obj.SetLabel('DESELECT') 
              mask = self._wxMaskId.GetValue().strip()
              for i in range(self._LB.GetCount()):
                  if mask:
                     if ( self._LB.GetString(i).startswith(mask) ):
                        self._LB.SetSelection(i)
                  else:
                     self._LB.SetSelection(i)  
           self._update_selection()        
       #--- update button
        else:  
           if self.pubsub:
             # print("BT: "+self.GetName().upper()+".UPDATE")
              pub.sendMessage(self.GetName().upper()+".UPDATE",id_list=self.ItemSelectedList)
           evt.Skip()      
         
    def listener(self,path=None,experiment=None,TMP=None):
        self.ID.path=path
        self._item_list=[]
        self._item_list = self.ID.update_meg_ids()
        #if self._item_list:        
        self.wx_update_lb()
                 
    def __get_ItemList(self):
        return self._ItemList
    def __set_ItemList(self,v):
        self._item_list = v
        self.wx_update_lb()
    ItemList = property(__get_ItemList,__set_ItemList)    
   
    def __get_ItemSelectedList(self):
        self._item_selected_list =[]
        for i in self._LB.GetSelections() :
            self._item_selected_list.append( self._LB.GetString(i) )
        return self._item_selected_list
    ItemSelectedList = property(__get_ItemSelectedList)    
           
    def _update_selection(self): 
        self._item_selected_list = self._LB.GetSelections()
        self._wxTxtIdInfo.SetLabel("%4d / %d" %( len(self._item_selected_list),self._LB.GetCount() ) )
        return self._item_selected_list
    
    def ClickOnDeSelect(self,evt):
        self._update_selection()
        
    def wx_update_lb(self):   
        self._LB.Clear()
        if self._item_list:
           self._LB.InsertItems(self._item_list,0)
        else:
           if self.stage: 
              wx.MessageBox("ERROR no directory found\n"+ self.stage, 'Error',  wx.OK | wx.ICON_ERROR)  
        self._update_selection()
        
    def update(self,stage=None,scan=None,data_type='mne'): #,experiment=None,TMP=None):
        if stage:
           self.stage = stage
        self._item_list=[]
        self._item_list = self.ID.update(scan=scan,data_type=data_type)
        self.wx_update_lb()
        pub.sendMessage(self.GetName().upper()+".UPDATE")

    def _ApplyLayout(self):
        ds  = 4
        ds1 = 1
        LEA = wx.LEFT|wx.EXPAND|wx.ALL
        REA = wx.RIGHT|wx.EXPAND|wx.ALL
        
        vbox = wx.BoxSizer(wx.VERTICAL)
      #--- Label + De/Selected IDs 
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add( wx.StaticText(self,0,label="I D s"),0,wx.LEFT,ds1)
        hbox1.Add((0,0),1,LEA,1)
        hbox1.Add( self._wxTxtIdInfo,0,LEA,ds1)
        vbox.Add(hbox1,0,LEA,ds)
        vbox.Add( wx.StaticLine(self),0,LEA,ds)
      #---  mask field 
        sbox = wx.StaticBox(self, -1,'MASK') 
        sz = wx.StaticBoxSizer(sbox, wx.VERTICAL)
        sz.Add(self._wxMaskId,0,REA, ds)        
      #---  
        vbox.Add(self._wxBtSelect,0,LEA,ds)
        vbox.Add(sz,  0,LEA,ds)
        vbox.Add(self._LB,        1,LEA,ds)
        vbox.Add(self._wxBtUpdate,0,LEA,ds)
                 
        self.SetSizer(vbox)   