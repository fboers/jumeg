#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys #path,fnmatch
import numpy as np

import wx
from   wx.lib.pubsub import pub
import wx.lib.scrolledpanel as scrolled
import wx.propgrid as wxpg
from   wx.propgrid import PropertyGridManager as wxpgm

#import PropertyGridManager

#--- jumeg cls
from jumeg.jumeg_base                                     import jumeg_base as jb
#--- jumeg wx stuff
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_frame           import JuMEG_MainFrame
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_panel           import JuMEG_wxMainPanel

#--- Merger CTRLs
from jumeg.gui.wxlib.jumeg_gui_wxlib_experiment_template  import JuMEG_wxExpTemplate
#from jumeg.gui.wxlib.jumeg_gui_wxlib_id_selection_box     import JuMEG_wxIdSelectionBox
#---
#from jumeg.gui.wxlib.jumeg_gui_wxlib_pbshost              import JuMEG_wxPBSHosts
#from jumeg.gui.jumeg_gui_wx_argparser                     import JuMEG_GUI_wxArgvParser
#---
#from jumeg.ioutils.jumeg_ioutils_subprocess               import JuMEG_IoUtils_SubProcess

__version__='2018-09-18.001'


class JuMEG_wxExperimentTemplatePanel(JuMEG_wxMainPanel):
      """
      """
      def __init__(self, parent,**kwargs):
          super().__init__(parent,name="JUMEG_MEEG_MERGER_PANEL")

          #self.module_path      = os.getenv("JUMEG_PATH") + "/jumeg/"
          #self.module_name      = "jumeg_merge_meeg"
          #self.module_extention = ".py"
          #self.SubProcess       = JuMEG_IoUtils_SubProcess()
          self._init(**kwargs)

      @property
      def fullfile(self): return self.module_path+"/"+self.module_name+ self.module_extention

      def init_pg(self,pnl):
          self.pgMan  = wxpgm(self.pnl_pg,-1,)
                          #style=wx.PG_BOLD_MODIFIED | wx.PG_SPLITTER_AUTO_CENTER | wx.PG_TOOLBAR | wx.PG_DESCRIPTION | wx.PG_COMPACTOR | wx.PGMAN_DEFAULT_STYLE )

          page = self.pgMan.AddPage("Experiment")
          page.Append(wxpg.PropertyCategory("Path"))
          #page.Append(wxpg.PGArrayStringEditorDialog("Stages"))
          #page.Append(wxpg.PGArrayStringEditorDialog("Scans"))

          page.Append(wxpg.IntProperty("Number", wx.propgrid.PG_LABEL, 1))
          page = self.pgMan.AddPage("Second Page")
          #page.Append(wx.propgrid.PG_LABEL("TEXT"))
          #page.Append(wx.propgrid.FontProperty("Font", wx.propgrid.PG_LABEL))

         # Display a header above the grid
          self.pgMan.ShowHeader()


      def update(self,**kwargs):
          self.stage  = kwargs.get("stage", os.getenv("JUMEG_PATH", os.getcwd()) + "/jumeg/" )
          #self.module = kwargs.get("module","jumeg_merge_meeg")
          #self.PDFs   = JuMEG_UtilsIO_PDFs()

          ds = 1
          LEA = wx.ALIGN_LEFT | wx.EXPAND | wx.ALL

          self.pnl_pg = scrolled.ScrolledPanel(self.PanelA.Panel, -1, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER)

          self.PGMPanel = wxpgm(self.pnl_pg.Panel,-1)
          vbox=wx.BoxSizer(wx.VERTICAL)
          vbox.Add(self.PGMPanel,1,LED,ds)
          self.pnl_pg.SetSizer(vbox)
          self.pnl_pg.SetAutoLayout(True)
          self.pnl_pg.Fit()

          #-- update wx CTRLs
          self.PanelA.SetTitle(v="PDF`s")
         # self.init_pg(self.PanelA.Panel)
          #self.PanelB.SetTitle(v="Parameter")
         #---

         #-- Top
          self.ExpTemplate = JuMEG_wxExpTemplate(self.TopPanel,ShowScan=False,ShowStage=False)
         # self.HostCtrl    = JuMEG_wxPBSHosts(self.TopPanel, prefix=self.GetName())
          self.TopPanel.GetSizer().Add(self.ExpTemplate, 1,LEA,ds)
          #self.TopPanel.GetSizer().Add(self.HostCtrl,0,LEA,ds)
         #--- A IDs;PDFs
          #self.IdSelectionBox = JuMEG_wxIdSelectionBox(self.PanelA.Panel, title='IDs')#, **kwargs)
          #self.PDFBox         = JuMEG_wxMEEG_PDFBox(self.PanelA.Panel, **kwargs)
          self.PanelA.Panel.GetSizer().Add(self.PGMPanel, 1, LEA,ds)
          self.PanelA.Panel.GetSizer().Add(self.pnl_pg, 1, LEA,ds)
          #self.PanelA.Panel.GetSizer().Add(self.PDFBox, 1, LEA, ds)
         # --- B  right
          #self.AP = JuMEG_GUI_wxArgvParser(self.PanelB.Panel, use_pubsub=self.use_pubsub, fullfile=self.fullfile,
          #                                 module=self.module_name, ShowParameter=True)
          #self.PanelB.Panel.GetSizer().Add(self.AP, 1, LEA,ds)
         #---
          self.Bind(wx.EVT_BUTTON, self.ClickOnButton)

         #print(self.ExpTemplate.TMP.template_data)


      def _update_hosts(self):
          pass

      def ClickOnExperimentTemplateSelect(self,experiment=None,TMP=None):
          """
          call update PropertyGrid

          Parameter
          ---------
           experiment:     stage / path to data
           TMP:     the template structure as dict

          """
          print("Experiment: "+experiment)
          print(TMP)
          print(TMP.template_data)

          exp_data=TMP.template_data['experiment']

          exp_page = self.PGMPanel.AddPage("Experiment")
          exp_page.Append( wxpg.PropertyCategory("1 - Experiment Global Properties") )
          exp_page.Append(wxpg.StringProperty(label="Name",name="PG_EXPERIMENT_NAME",value=exp_data.get('name',"TEST") ))

          exp_page.Append(wxpg.ArrayStringProperty(label="Stages",name="PG_EXPERIMENT_STAGES",value=exp_data.get('stages',[]   ) ))
          exp_page.Append(wxpg.ArrayStringProperty(label="Scans", name="PG_EXPERIMENT_SCANS", value=exp_data.get('scans', []   ) ))
          exp_page.Append(wxpg.ArrayStringProperty(label="Bads",  name="PG_EXPERIMENT_BADS",  value=exp_data.get('bads_list',[]) ))
          id_list = exp_data.get('ids',[])
          exp_page.Append(wxpg.ArrayStringProperty(label="Ids",   name="PG_EXPERIMENT_IDS",   value=[ str(x) for x in id_list ] ))

          exp_page.Append( wxpg.PropertyCategory("2 - Experiment Path Properties") )
          path_data=TMP.template_data['experiment']
          for p in ['mne','eeg','empty_room','doc','source','stimuli']:
              exp_page.Append(wxpg.StringProperty(label=p,name="PG_EXPERIMENT_PATH_"+p.upper(),value=path_data.get(p,p) ))


          #IntProperty("Number", wx.propgrid.PG_LABEL, 1))

          #page.Append(wxpg.PropertyCategory("Path"))
          #page.Append(wxpg.PGArrayStringEditorDialog("Stages"))
          #page.Append(wxpg.PGArrayStringEditorDialog("Scans"))


          #page = self.pgMan.AddPage("Second Page")
          #page.Append(wx.propgrid.PG_LABEL("TEXT"))
          #page.Append(wx.propgrid.FontProperty("Font", wx.propgrid.PG_LABEL))

         # Display a header above the grid
          self.PGMPanel.ShowHeader()

          """
          {'info': {'time': '2018-03-20  00:00:01', 'user': 'fboers', 'version': 'v2018-03-20-001'},
           'experiment': {'name': 'FREVIEWING', 'ids': [], 'scans': ['FREEVIEW01'],
           'stages': ['/mnt/meg_store1/exp/FREEVIEWING', '/data/meg_store1/exp/FREEVIEWING', '/home/fboers/MEGBoers/data/exp/FREEVIEWING'],
           'bads_list': ['MEG 007', 'MEG 010', 'MEG 142', 'MEG 156', 'RFM 011'],
           'path': {'experiment': '/mnt/meg_store1/exp/FREEVIEWING', 
                     'mne': 'mne', 
                     'empty_room': 'empty_room',
                     'eeg': 'eeg',
                     'mft': 'mft',
                     'doc': 'doc', 
                     'source': 'source', 
                     'stimuli': 'stimuli'},
           'mri': {'path': {'dicom': 'mrdata/dicom', 'mrdata': 'mrdata', 'mri_orig': 'mrdata/mri_orig', 'segmentation': 'mrdata/segmentation', 'freesurfer': 'mrdata/freesurfer'}}}
          """


          #self.IdSelectionBox.update(stage=stage,scan=scan,data_type=data_type)
          #self.PDFBox.update(reset=True)

      def init_pubsub(self, **kwargs):
          """ init pubsub call overwrite """
          pub.subscribe(self.ClickOnApply,self.GetName().upper()+".BT_APPLY")
          pub.subscribe(self.ClickOnExperimentTemplateSelect,'EXPERIMENT_TEMPLATE.SELECT')

    #---
      def Cancel(self):
          print("CLICK ON CANCEL")

      def ClickOnApply(self):
          """
          apply to subprocess

          """
          pass

      def ClickOnButton(self, evt):
          obj = evt.GetEventObject()

          if obj.Label == "CLOSE":
             pub.sendMessage('MAIN_FRAME.CLICK_ON_CLOSE',evt=evt)
          if obj.Label == "CANCEL":
             pub.sendMessage('MAIN_FRAME.CLICK_ON_CANCEL',evt=evt)
          if obj.Label == "APPLY":
             self.ClickOnApply()
          else:
             evt.Skip()

class JuMEG_GUI_ExperimentTemplateFrame(JuMEG_MainFrame):
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=[1024,768],name='JuMEG Experiment Template',*kargs,**kwargs):
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
        self.MenuBar.DestroyChildren()
        self._init_MenuDataList()
        self._update_menubar()
        self.AddLoggerMenu(pos=1,label="Logger")
   #---
    def update(self,**kwargs):
       #---
        self.UpdateAboutBox()
       #---
        self._init_MenuDataList()
       #---
        return JuMEG_wxExperimentTemplatePanel(self,name="JuMEG_EXPERIMENT_TEMPLATE_PANEL",**kwargs)
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
   frame = JuMEG_GUI_ExperimentTemplateFrame(None,-1,'JuMEG Experiment Template FZJ-INM4',debug=True,verbose=True)
   app.MainLoop()
