#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 14:14:42 2018

@author: fboers
-------------------------------------------------------------------------------
Updates:
2018-08-27: more help-docs
    

"""

import wx
from wx.lib.pubsub import pub
from jumeg.template.jumeg_template import JuMEG_Template_Experiments
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxControlGrid

__version__='2018-08-27.001'

class JuMEG_wxExpTemplate(wx.Panel):
    """
     JuMEG_wxExpTemplate
     select Experiment Template [M100] and stage directory [/data/xyz/exp/M100] from Exp Template folder
     
     Paremeters:
     -----------    
      parent widged 
      template_path: path to experiment templates
      pubsub       : use wx.pupsub msg systen <False>
                     example: pub.sendMessage('EXPERIMENT_TEMPLATE',stage=stage,experiment=experiment,TMP=template_data)
                     or button event from  <ExpTemplateApply> button for apply/update   
      verbose      : <False>
      bg           : backgroundcolor <grey90>

      ShowExp   : show Experiment combobox <True>
      ShowScan  : show Scan combobox       <True>
      ShowStage : show Stage combobox      <True>

    """
    def __init__(self,parent,template_path=None,name="JUMEG_WX_EXP_TEMPLATE",**kwargs):
        super(JuMEG_wxExpTemplate, self).__init__(parent)
        self.TMP = JuMEG_Template_Experiments()
        self._init(**kwargs)

    @property
    def wxExpBt(self): return self.FindWindowByName("BT.EXPERIMENT")
    @property
    def wxExpCb(self): return self.FindWindowByName("CB.EXPERIMENT")

    @property
    def wxExpScanBt(self): return self.FindWindowByName("BT.SCAN")
    @property
    def wxExpScanCb(self): return self.FindWindowByName("CB.SCAN")

    @property
    def wxExpStageBt(self): return self.FindWindowByName("BT.STAGE")
    @property
    def wxExpStageCb(self): return self.FindWindowByName("CB.STAGE")

    @property
    def wxExpUpdateBt(self): return self.FindWindowByName("BT.UPDATE")

    @property
    def verbose(self): return self.TMP.verbose
    @verbose.setter
    def verbose(self,v): self.TMP.verbose = v
    
    @property
    def stage(self): return self.TMP.isPath( self.wxExpStageCb.GetValue() )

    @property
    def exp(self):   return self.wxExpCb.GetValue()
  
    @property   
    def experiment(self): return self.wxExpCb.GetValue()
  
    @property   
    def scan(self): return self.wxExpScanCb.GetValue()
  
    @property    
    def tmp_data(self): return self.TMP.template_data

    @property
    def template_path(self): return self.TMP.template_path
    @template_path.setter
    def template_path(self,v): self.TMP.template_path=v

    def _init(self, **kwargs):
        """" init """
        self._update_from_kwargs(**kwargs)
        self._wx_init()
        self.update(**kwargs)
        self._ApplyLayout()

    def _wx_init(self):
        """ init WX controls """
        self.SetBackgroundColour(self.bg)
       # --- PBS Hosts
        ctrls = []
        if self.ShowExp:
           ctrls.append(("BT",   "BT.EXPERIMENT", "Experiment", "update experiment template list",None))
           ctrls.append(("COMBO","CB.EXPERIMENT", "COMBO_EXPERIMENT", [], "select experiment templatew",None))

        if self.ShowScan:
           ctrls.append(("BT",   "BT.SCAN", "SCAN", "select scan",None))
           ctrls.append(("COMBO","CB.SCAN", "SCAN", [], "select experiment template",None))

        if self.ShowStage:
           ctrls.append(("FLBT", "BT.STAGE", "Stage", "select stage", None))
           ctrls.append(("COMBO","CB.STAGE", "STAGE", [], "select experiment satge",None))
           ctrls.append(("BT",   "BT.UPDATE", "Update", "update",None))

        self.pnl = JuMEG_wxControlGrid(self, label=None, drawline=False, control_list=ctrls, cols=len(ctrls) + 4,AddGrowableCol=[1,3,5])
        self.pnl.SetBackgroundColour(self.bg_pnl)

        for n in ["EXPERIMENT","SCAN","UPDATE"]:
            try:
                self.FindWindowByName("BT."+n).Disable()
            except:
                pass
        for n in["EXPERIMENT","SCAN","STAGE"]:
            try:
                self.FindWindowByName("CB."+n).Enable(False)
            except:
                pass

       #--- bind CTRLs in class
        self.Bind(wx.EVT_BUTTON,  self.ClickOnButton)
        self.Bind(wx.EVT_COMBOBOX,self.ClickOnComBoBox)

    def _update_from_kwargs(self,**kwargs):
        self.template_path = kwargs.get("template_path",self.TMP.template_path)
        self.verbose       = kwargs.get("verbose",self.verbose)
        self.pubsub        = kwargs.get("pubsub",True)
        self.bg            = kwargs.get("bg",    wx.Colour([230, 230, 230]))
        self.bg_pnl        = kwargs.get("bg_pnl",wx.Colour([240, 240, 240]))
       #---
        self.ShowExp   = kwargs.get("ShowExp",  True)
        self.ShowScan  = kwargs.get("ShowScan", True)
        self.ShowStage = kwargs.get("ShowStage",True)

    def update(self,**kwargs):
        """ update  kwargs and widgets """
        self._update_from_kwargs(**kwargs)
        self.UpdateExperimentComBo()
        self.wxExpBt.Enable(True)
        self.UpdateStageComBo( self.wxExpCb.GetValue() )
        if self.wxExpUpdateBt:
           self.wxExpUpdateBt.Enable(True)
        if self.wxExpScanBt:
           self.wxExpScanBt.Enable(True)
        if self.wxExpScanCb:
           self.wxExpScanCb.Enable(True)

    def UpdateExperimentComBo(self):
        """ update experiment combobox if selected """
        self.UpdateComBo(self.wxExpCb,self.UpdateTemplateList())
        self.UpdateTemplateList()
        self.wxExpCb.SetToolTip(wx.ToolTip("Template path: {}".format(self.TMP.template_path) ))
        if self.verbose:
           self.TMP.pp(self.TMP.template_name_list,head="Template path: "+self.TMP.template_path)
    
    def UpdateStageComBo( self,exp ):
        """ update stage """
        self.UpdateTemplate( exp )

        if self.TMP.template_data:
           stage_list=[]
          #--- stage stuff to combobox
           self.UpdateComBo(self.wxExpStageCb,self.TMP.template_data['experiment']['stages'] )
           if self.wxExpStageCb:
              self.wxExpStageCb.SetValue(self.wxExpStageCb.GetItems()[0])
         #---  ck is dir
           msg=[]
          # for p in self.wxExpStageComBo.GetItems():
          #     if not self.TMP.isPath(p,print_error=False):
          #        msg.append(p )
          # if msg:
          #    msg.insert(0,"!!! Error : no such path or directory:")
          #    print("ERROR: ".format(msg))
          #    pub.sendMessage("MAIN_FRAME.MSG.ERROR",msgtxt=msg )
         #---
           try:
              if isinstance( self.TMP.template_data['experiment']['scans'], (list)):
                 scan_list = sorted( self.TMP.template_data['experiment']['scans'] )
              else:
                 scan_list=[ self.TMP.template_data['experiment']['scans'] ]
           except:  
                 scan_list=[ self.TMP.template_data['experiment']["name"] ] 

           self.UpdateComBo( self.wxExpScanCb,scan_list )

           if self.wxExpStageCb:
              self.wxExpStageCb.SetValue( scan_list[0]  )
           
       #--- enable STAGE bt
           if self.wxExpStageBt:
              self.wxExpStageBt.Enable(True)
           #self.UpdateComBo(self.wxExpStageCb,[])
           #self.UpdateComBo(self.wxExpScanCb,[])
           #if self.wxExpStageBt:
           #   self.wxExpStageBt.Enable(False)

           if self.pubsub:
              pub.sendMessage('EXPERIMENT_TEMPLATE.SELECT', experiment=self.experiment, TMP=self.TMP)

    #---
    def UpdateComBo(self, cb, vlist, sort=True):
        """
        update wx.ComboBox: clear,SetItems,SetValue first element in list
        remove double items and sort list

        Parameters:
        -----------
        combobox obj
        list to insert
        sort : will sort list <True>
        """

        if not cb: return

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

    def ClickOnButton(self,evt):
        """ click on button event """
        obj = evt.GetEventObject()
      #--- ExpBt
        if obj.GetName() == "BT.EXPERIMENT":
           self.update() 
      #--- ExpStageBt start change Dir DLG
        if obj.GetName() == "BT.STAGE":
           dlg = wx.DirDialog(None,"Choose Stage directory","",wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
           dlg.SetPath( self.wxExpStageCb.GetValue() )
           if (dlg.ShowModal() == wx.ID_OK):
              if self.TMP.template_data:
                 l=[dlg.GetPath()]
                 l.extend(self.TMP.template_data['experiment']['path']['stage'])
                 self.UpdateComBo(self.wxExpStageCb, l )
           dlg.Destroy()
      #--- ExpBt 
        if obj.GetName() == "BT.UPDATE":
           if self.pubsub:
              pub.sendMessage('EXPERIMENT_TEMPLATE.UPDATE',stage=self.stage,scan=self.scan,data_type='mne')  #experiment=self.experiment,TMP=self.template_data
           else: evt.Skip()
                 
    def ClickOnComBoBox(self,evt):
        """ click on combobox event"""
        obj = evt.GetEventObject()
       #--- ExpComBo
        if obj.GetName() == "CB.EXPERIMENT":
           self.UpdateStageComBo( obj.GetValue() )

  #--- todo new CLS  
    def UpdateTemplateList(self):
        """ update template list
        Result
        -------
         template list
        """
        self.TMP.template_update_name_list()
        return self.TMP.template_name_list
       
    def UpdateTemplate(self,exp,path=None,verbose=False):
        """ update a JuMEG template
         
        Parameters
        ----------
         exp    : name of experiment
         path   : <None>
         verbose:<false>
         
        Result
        ------
         template data dict
        """
        #print( "Experiment Template -> "+exp)
        self.TMP.template_name = exp
        if path:
           self.TMP.template_path = path
        self.TMP.verbose = verbose      
        self.TMP.template_update_file()
        #print("TEMP data: ".format(self.TMP.template_data))
        return self.TMP.template_data

  #---      
    def _ApplyLayout(self):
        """ Apply Layout via wx.GridSizers"""
       #--- Label + line
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add( self.pnl,1, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,2)
        self.SetSizer(vbox)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()

