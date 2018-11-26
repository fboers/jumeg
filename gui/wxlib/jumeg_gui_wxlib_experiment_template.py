#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 27 14:14:42 2018

@author: fboers
-------------------------------------------------------------------------------
Updates:
2018-08-27.001 new structure, refrac
    

"""

import wx,sys
from wx.lib.pubsub import pub
from jumeg.template.jumeg_template import JuMEG_Template_Experiments
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxControlGrid

__version__='2018-08-27.001'


class JuMEG_ExpTemplate(JuMEG_Template_Experiments):
   def __init__(self,**kwargs):
       super().__init__()

   @property
   def name(self ): return self.template_data['experiment']['name']
   @property
   def scans(self): return self.template_data['experiment']['scans']

   @property
   def stages(self):return self.template_data['experiment']['stages']
   @stages.setter
   def stages(self,v):
       if isinstance(v,(list)):
          self.template_data['experiment']['stages']=v
       else:
          self.template_data['experiment']['stages'].append(v)

   def update_from_kwargs( self, **kwargs ):
       self.template_path = kwargs.get("template_path", self.template_path)
       self._pubsub_error_msg = kwargs.get("pubsub_error_msg", "MAIN_FRAME.MSG.ERROR")

   def _init( self, **kwargs ):
       self.update_from_kwargs(**kwargs)

   def get_sorted_experiments(self,issorted=True):
       """
       Result
       -------
        sorted list of scans
       """
       exps = self.template_update_name_list()
       if issorted:
          return sorted( exps )
       return exps

   def get_sorted_scans(self,issorted=True):
       """
       Result
       -------
        sorted list of scans
       """
       try:
           if isinstance( self.scans, (list)):
              if issorted:
                 return sorted( self.scans )
              return self.scans
           else:
              return [ self.scans ]

       except:
           return []

   def template_check_experiment_data(self):
        """
        check's template for <experiment> structure e.g.:
        "experiment":{
              "name"  : experiment name,
              "scans" :[ list of scans],
              "stages":[ list of start dirs]
              }
        Result:
        -------
        True/False
        """
        error_msg=[]
        if not self.template_data:
           error_msg.append("No template data found : " + self.template_full_filename)
        elif not self.template_data.get('experiment',None):
           error_msg.append("No <experiment> structure found : "+self.template_name)
        else:
           exp = self.template_data.get('experiment',None)
           for k in["scans","stages"]:
               if not exp.get(k):
                  error_msg.append("No <{}>  found".format(k))
           if error_msg:
              error_msg.insert(0,"Checking Experiment Template")
              error_msg.append("Module  : "+sys._getframe(1).f_code.co_name )
              error_msg.append("Function: check_experiment_template_data")
              pub.sendMessage(self._pubsub_error_msg,data=error_msg)
              return False
        return True

   def template_update(self,exp,path=None,verbose=False):
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
        self.template_name = exp
        if path:
           self.template_path = path
        self.verbose = verbose
        self.template_update_file()

        if self.template_check_experiment_data():
           return self.template_data
        return False


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
    def __init__(self,parent,name="JUMEG_WX_EXPERIMENT_TEMPLATE",**kwargs):
        super().__init__(parent)
        self.TMP = JuMEG_ExpTemplate(**kwargs)
        self._ctrl_names     = ["EXPERIMENT", "SCAN","STAGE","UPDATE"]
        self.prefixes        = ["BT.","CB."]
        self._pubsub_messages={"UPDATE":"UPDATE"}

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

    def GetExperiment(self):
        return self.wxExpCb.GetValue()

    def GetScan(self):
        return self.wxExpScanCb.GetValue()

    def GetStage( self ):
        return self.TMP.isPath(self.wxExpStageCb.GetValue())

  # --- pubsub msg
  #--- ToDO new CLS
    def GetMessageKey( self, msg ):    return self._pubsub_messages.get(msg.upper())
    def SetMessageKey( self, msg, v ): self._pubsub_messages[msg] = v.upper()

    def GetMessage( self, msg ): return self.GetName()+ "." +self.GetMessageKey(msg)

    def send_message(self,msg,evt):
        """ sends a pubsub msg, can change the message via <MessageKey> but not the arguments
           "EXPERIMENT_TEMPLATE.UPDATE",stage=self.GetStage(),scan=self.GetScan(),data_type='mne'
        """
        if self.pubsub:
           pub.sendMessage(self.GetMessage(msg),stage=self.GetStage(),scan=self.GetScan(),data_type='mne')
        else: evt.Skip()

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
           ctrls.append(("COMBO","CB.STAGE", "Stage", [], "select experiment satge",None))
           ctrls.append(("BT",   "BT.UPDATE","Update", "update",None))

        self.CtrlGrid = JuMEG_wxControlGrid(self, label=None, drawline=False, control_list=ctrls, cols=len(ctrls) + 4,AddGrowableCol=[1,3,5])
        self.CtrlGrid.SetBackgroundColour(self.bg_pnl)

        self.CtrlGrid.EnableDisableCtrlsByName(self._ctrl_names,False,prefix=self.prefixes)

       #--- bind CTRLs in class
        self.Bind(wx.EVT_BUTTON,  self.ClickOnCtrl)
        self.Bind(wx.EVT_COMBOBOX,self.ClickOnCtrl)

    def _update_from_kwargs(self,**kwargs):
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
        self.UpdateScanStageComBo( experiment = self.wxExpCb.GetValue() )

    def UpdateExperimentComBo(self):
        """ update experiment combobox if selected """
        self.CtrlGrid.UpdateComBox(self.wxExpCb,self.TMP.get_sorted_experiments())
        self.CtrlGrid.EnableDisableCtrlsByName(self._ctrl_names[0], True, prefix=self.prefixes)  # experiment ctrl first
        self.wxExpCb.SetToolTip(wx.ToolTip("Template path: {}".format(self.TMP.template_path) ))
        if self.verbose:
           wx.LogMessage( self.TMP.pp_list2str(self.TMP.template_name_list,head="Template path: "+self.TMP.template_path))

    def UpdateScanComBo( self,scan_list=None ):
        """
        :param scan_list:
        :return:
        """
        if not scan_list:
           scan_list = self.TMP.get_sorted_scans()
        self.CtrlGrid.UpdateComBox( self.wxExpScanCb,scan_list )
        state = bool(len(scan_list))
        if state:
           self.wxExpStageCb.SetValue( scan_list[0]  )

        self.CtrlGrid.EnableDisableCtrlsByName(self._ctrl_names[1],state,prefix=self.prefixes)

    def UpdateStageComBo(self,stage_list=None):
        """
        :param stage_list:
        :return:
        """
        if not stage_list:
           stage_list = self.TMP.stages
        self.CtrlGrid.UpdateComBox(self.wxExpStageCb, stage_list)
        state = bool(len(stage_list))
        if state:
           self.wxExpStageCb.SetValue(self.wxExpStageCb.GetItems()[0])
        self.CtrlGrid.EnableDisableCtrlsByName(self._ctrl_names[2:],state, prefix=self.prefixes)

    def UpdateScanStageComBo( self,experiment=None ):
        """
        fill scan

        Parameter
        ---------
         experiment name
        """
        if experiment:
           self.TMP.template_update( experiment )

           if self.ShowScan:
              self.UpdateScanComBo()
           if self.ShowStage:
              self.UpdateStageComBo()
        else:
            self.CtrlGrid.UpdateComBox(self.wxExpScanCb, [])
            self.CtrlGrid.UpdateComBox(self.wxExpStageCb,[])
            self.EnableDisableCtrlsByName(self._ctrl_names[1:],status=False,prefix=self.prefixes)
   #---
    def ClickOnCtrl(self,evt):
        """ click on button or combobox send event
        """
        obj = evt.GetEventObject()
       #--- ExpComBo
        if obj.GetName() == "CB.EXPERIMENT":
           self.UpdateScanStageComBo( obj.GetValue() )
       #--- ExpBt
        elif obj.GetName() == "BT.EXPERIMENT":
           self.update() 
       #--- ExpStageBt start change Dir DLG
        elif obj.GetName() == "BT.STAGE":
           dlg = wx.DirDialog(None,"Choose Stage directory","",wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST)
           dlg.SetPath( self.wxExpStageCb.GetValue() )
           if (dlg.ShowModal() == wx.ID_OK):
              if self.TMP.template_data:
                 l=[dlg.GetPath()]
                 l.extend(self.TMP.stages)
                 self.UpdateComBo(self.wxExpStageCb, l )
           dlg.Destroy()
      #--- ExpBt 
        elif obj.GetName() == "BT.UPDATE":
           self.send_message("UPDATE",evt)
        else:
            evt.Skip()

  #---      
    def _ApplyLayout(self):
        """ Apply Layout via wx.GridSizers"""
       #--- Label + line
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add( self.CtrlGrid,1, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL,2)
        self.SetSizer(vbox)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()

