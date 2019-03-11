#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
JuMEG GUI to merge MEG (FIF) and EEG data (BrainVision)
call <jumeg_merge_meeeg> with meg and eeg file and parameters
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
import os,sys
import numpy as np

import wx
from   wx.lib.pubsub import pub
# import wx.lib.scrolledpanel as scrolled

#--- jumeg cls
from jumeg.jumeg_base                                     import jumeg_base as jb
#--- jumeg wx stuff
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_frame           import JuMEG_wxMainFrame
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_panel           import JuMEG_wxMainPanel
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxSplitterWindow,JuMEG_wxCMDButtons,JuMEG_wxControlGrid,JuMEG_wxControlButtonPanel

#--- Experiment Template
from jumeg.gui.wxlib.jumeg_gui_wxlib_experiment_template  import JuMEG_wxExpTemplate
#---Merger CTRLs
from jumeg.gui.wxlib.jumeg_gui_wxlib_psel                 import JuMEG_wxPselFIF
#---
from jumeg.gui.wxlib.jumeg_gui_wxlib_pbshost              import JuMEG_wxPBSHosts
from jumeg.gui.jumeg_gui_wx_argparser                     import JuMEG_GUI_wxArgvParser
#---
from jumeg.ioutils.jumeg_ioutils_subprocess               import JuMEG_IoUtils_SubProcess

__version__="2019-02-11-001"

class JuMEG_wxFIFCtrlGrid(wx.Panel):
    def __init__(self,parent,*kargs,**kwargs):
        super().__init__(parent,*kargs)
        self._names = {"stage_ck" :"CK_STAGE","stage_txt":"TXT_STAGE",
                       "fif_postfix_txt":"TXT_POSTFIX"}
        self._ctrl_gird = None
        self._init(**kwargs)
    
    @property
    def CtrlGrid(self):
        return self._ctrl_grid
    
    #--- fif stage txt
    @property
    def StagePostfix(self):
        return self._get_ctrl("stage_txt").GetValue()
    
    @StagePostfix.setter
    def StagePostfix(self,v):
        self._get_ctrl("stage_txt").SetValue(v)
    
    #--- fif stage ck
    @property
    def UseStagePostfix(self):
        return self._get_ctrl("stage_ck").GetValue()
    
    @UseStagePostfix.setter
    def UseStagePostfix(self,v):
        self._get_ctrl("stage_ck").SetValue(v)
    
    #--- emptyroom txt
    @property
    def FIFPostfix(self):
        return self._get_ctrl("fif_postfix_txt").GetValue()
    
    @FIFPostfix.setter
    def FIFPostfix(self,v):
        self._get_ctrl("fif_postfix_txt").SetValue(v)
        
    def _get_name(self,k):
        return self._names[k]
    
    def _get_ctrl(self,k):
        return self.FindWindowByName(self.GetName().upper() + "." + self._names[k])
        
    def _init(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        self._wx_init(**kwargs)
        self.FIFPostfix = kwargs.get("fif_postfix","-raw.fif")
        self._ApplyLayout()
    
    def _update_from_kwargs(self,**kwargs):
        self.SetName(kwargs.get("name","FIF_CTRL"))
        
    def _wx_init(self,**kwargs):
       #---  export parameter -> CLS
        ctrls = [
            ["CK",self._get_name("stage_ck"),"Stage Postfix",True,"add postfix to fif stage <experiment name>/mne", None],
            ["TXT",self._get_name("stage_txt"),"","postfix append to fif stage <experiment name>/mne",None],
            ["FLBT","FIF_FTBT","FIF postfix","postfix to search for <-raw.fif>",None],
            ["TXT",self._get_name("fif_postfix_txt"),"","fif postfix to search for",None]]
         
        for i in range(len(ctrls)):
            if ctrls[i][1].startswith(ctrls[i][0]):  #TXT CK
                ctrls[i][1] = self.GetName().upper() + "." + ctrls[i][1]
            else:
                ctrls[i][1] = self.GetName().upper() + "." + ctrls[i][0] + "_" + ctrls[i][1]
        
        self._ctrl_grid = JuMEG_wxControlGrid(self,label="",drawline=False,control_list=ctrls,cols=2,
                                              AddGrowableCol=[1],set_ctrl_prefix=False)
        self._ctrl_grid.SetBackgroundColour("grey90")
        
        self.Bind(wx.EVT_COMBOBOX,self.ClickOnCtrls)
        self.Bind(wx.EVT_CHECKBOX,self.ClickOnCtrls)
    
    #---
    def ClickOnCtrls(self,evt):
        """ pass to parent event handlers """
        evt.Skip()
    
    def _ApplyLayout(self):
        """ default Layout Framework """
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.CtrlGrid,1,wx.ALIGN_LEFT | wx.EXPAND | wx.ALL,1)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()


class JuMEG_wxEpocherPanel(JuMEG_wxMainPanel):
      """
      GUI Panel to merge EEG and MEG data into MNE fif format
      """

      def __init__(self, parent,name="JUMEG_EPOCHER",**kwargs):
          super().__init__(parent,name=name,ShowTitleB=False)
      
          self.ShowCmdButtons   = True
          self.ShowTopPanel     = True
          self.ShowTitleA       = True
          self.ShowTitleB       = True
          self.ShowMinMaxBt     = True
          self.module_path      = os.getenv("JUMEG_PATH") + "/jumeg/pipeline/"
          self.module_name      = "jumeg_preproc_epocher"
          self.module_extention = ".py"
          self.SubProcess       = JuMEG_IoUtils_SubProcess()
          self._template_panel_name = "EXPERIMENT_TEMPLATE"
          self._init(**kwargs)

      @property
      def fullfile(self): return self.module_path+"/"+self.module_name+ self.module_extention

      def update(self,**kwargs):
          self.stage  = kwargs.get("stage", os.getenv("JUMEG_PATH", os.getcwd()) + "/jumeg/pipeline" )
        #-- update wx CTRLs
          self.PanelA.SetTitle(v="PDF`s")
        #---
          ds=1
          LEA = wx.ALIGN_LEFT | wx.EXPAND | wx.ALL
         #-- Top
          self.ExpTemplate = JuMEG_wxExpTemplate(self.TopPanel,name=self.GetName()+"."+self._template_panel_name)
          self.HostCtrl    = JuMEG_wxPBSHosts(self.TopPanel, prefix=self.GetName())
          self.TopPanel.GetSizer().Add(self.ExpTemplate,3,LEA,ds)
          self.TopPanel.GetSizer().Add(self.HostCtrl,1, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL,ds)
         #--- A IDs;PDFs
          self.PDFBox = JuMEG_wxPselFIF(self.PanelA.Panel,name=self.GetName()+".PDFBOX_EPOCHER",**kwargs)
          self.PanelA.Panel.GetSizer().Add(self.PDFBox, 1, LEA,ds)
         # --- B  right
          fif_pnl = wx.Panel(self.PanelB.Panel,-1)
         #--- bti ctrl parameter , stage,emptyroom
          self.FIFCtrl = JuMEG_wxFIFCtrlGrid(fif_pnl,name=self.GetName() + ".FIF_CTRL")
         #--- import parameter
          self.AP = JuMEG_GUI_wxArgvParser(fif_pnl,name=self.GetName() + ".AP",use_pubsub=self.use_pubsub,
                                           fullfile=self.fullfile,
                                           module=self.module_name,ShowParameter=True)

          vbox = wx.BoxSizer(wx.VERTICAL)
          vbox.Add(self.FIFCtrl,0,LEA,ds)
          vbox.Add(self.AP,1,LEA,ds)
          fif_pnl.SetAutoLayout(True)
          fif_pnl.SetSizer(vbox)
          fif_pnl.Fit()

          self.PanelB.Panel.GetSizer().Add(fif_pnl,1,LEA,ds)
          self.PanelB.SetTitle("FIF & MNE Parameter")

          #---
          self.Bind(wx.EVT_BUTTON, self.ClickOnCtrls)
          self.update_argparser_parameter()
     
      def update_on_display(self):
          self.SplitterAB.SetSashPosition(self.GetSize()[0] / 2.0,redraw=True)

      def update_parameter(self):
          """
          update argparser default parameter from template
          set choices in BTiCTLs, set value to first item
          """
          for k in self.ExpTemplate.TMP.bti_data.keys():
              #print(k)
              #print(self.ExpTemplate.TMP.bti_data.get(k))
              self.AP.update_parameter(k,self.ExpTemplate.TMP.bti_data.get(k))
          self.FIF.StagePostfix = self.ExpTemplate.TMP.name + "/mne"
         

      def init_pubsub(self,**kwargs):
          """ init pubsub call overwrite """
          #pub.subscribe(self.ClickOnExperimentTemplateSelectExperiment,self.ExpTemplate.GetMessage("SELECT_EXPERIMENT"))
          pub.subscribe(self.ClickOnExperimentTemplateUpdate,self.ExpTemplate.GetMessage("UPDATE"))

      def ClickOnExperimentTemplateSelectExperiment(self,stage=None,scan=None,data_type=None):
          """

          :param stage:
          :param scan:
          :param data_type:
          :return:
          """
          self.update_parameter()


      def ClickOnExperimentTemplateUpdate(self,stage=None,scan=None,data_type=None):
          """

          :param stage:
          :param scan:
          :param data_type:
          :return:
          """
          self.AP.SetParameter(pdf_stage=self.FIFCtrl.StartPath)
          self.PDFBox.update(stage=self.FIFCtrl.StartPath,scan=scan, #,pdf_name=self.AP.GetParameter("pdf_fname"),
                             verbose=self.verbose,debug=self.debug)

      def update_argparser_parameter(self):
          """ update parameter BADS_LIST from template"""
          pass
           
     
      def ClickOnApply(self):
          """
          get selected pdfs structure
          make commands with argparser parameter
          apply cmds to subprocess

          """
         
          self.PDFBox.verbose = self.verbose
          pdfs = self.PDFBox.GetSelectedPDFs()
          if not pdfs :
             wx.CallAfter( pub.sendMessage,"MAIN_FRAME.MSG.ERROR",data="\n MEEG Merger: Please select PDFs first")
             return
     
          #cmd_parameter       = self.AP.GetParameter()
          cmd_command = self.AP.get_fullfile_command(ShowFileIO=True)
          joblist     = []

         #--- del  "stage"
          #cmd_list = cmd_command.split()
          #for k in ["--meg_stage","--eeg_stage","-smeg","-seeg","--list_path"]:
          #    for idx in range(len(cmd_list)):
          #        if cmd_list[idx].startswith(k):
          #           del cmd_list[idx]
          #           break
          
          cmd_command = " ".join(cmd_list)
          print(cmd_command)
          
          for subject_id in pdfs.get('mne'):
              for idx in range( len( pdfs['mne'][subject_id] ) ):
                  if not pdfs['mne'][subject_id][idx]["selected"]: continue
                  cmd  = cmd_command
                  #eeg_idx = pdfs["eeg_index"][subject_id][idx]
                  #cmd += " --meg_stage=" + pdfs["stage"]
                  #cmd += " -fmeg " + pdfs["mne"][subject_id][idx]["pdf"]
                  #cmd += " --eeg_stage=" + pdfs["stage"]
                  #cmd += " -feeg " + pdfs["eeg"][subject_id][eeg_idx]["pdf"]
                  #cmd += " "+ cmd_parameter
                  joblist.append( cmd )
           
          if self.verbose:
             wx.LogMessage(jb.pp_list2str(joblist, head="MEEG Merger Job list: "))
             wx.LogMessage(jb.pp_list2str(self.HostCtrl.HOST.GetParameter(),head="HOST Parameter"))
          if joblist:
            # wx.CallAfter(pub.sendMessage,"SUBPROCESS.RUN.START",jobs=joblist,host_parameter=self.HostCtrl.HOST.GetParameter(),verbose=self.verbose)
             wx.CallAfter(self.SubProcess.run,jobs=joblist,host_parameter=self.HostCtrl.HOST.GetParameter(),verbose=self.verbose)
             
      def ClickOnCancel(self,evt):
          wx.LogMessage( "<Cancel> button is no in use" )
          wx.CallAfter( pub.sendMessage,"MAIN_FRAME.MSG.INFO",data="<Cancel> button is no in use")

      def ClickOnCtrls(self, evt):
          obj = evt.GetEventObject()
          print(obj.GetName())
          if obj.GetName() == self.GetName()+".BT.APPLY":
             self.ClickOnApply()
          elif obj.GetName() == self.GetName()+".BT.CLOSE":
             wx.CallAfter( pub.sendMessage, "MAIN_FRAME.CLICK_ON_CLOSE",evt=evt)
          #else:
          #   evt.Skip()

class JuMEG_GUI_EpocherFrame(JuMEG_wxMainFrame):
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=[1024,768],**kwargs):
        style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
        super().__init__(parent,id, title, pos, size, style,**kwargs)
        self.template_path = None

    def update(self,**kwargs):
        return JuMEG_wxEpocherPanel(self,**kwargs)
       
    def UpdateAboutBox(self):
        self.AboutBox.description = "Epocher>"
        self.AboutBox.version     = __version__
        self.AboutBox.copyright   = '(C) 2018 Frank Boers <f.boers@fz-juelich.de>'
        self.AboutBox.developer   = 'Frank Boers'
        self.AboutBox.docwriter   = 'Frank Boers'

if __name__ == '__main__':
   app = wx.App()
   frame = JuMEG_GUI_EpocherFrame(None,-1,'JuMEG Epocher',module="jumeg_preproc_epocher",function="get_args",ShowLogger=True,ShowCmdButtons=True,ShowParameter=True,debug=True,verbose=True)
   app.MainLoop()
