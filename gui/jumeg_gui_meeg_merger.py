#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys #path,fnmatch
import numpy as np

import wx
from   wx.lib.pubsub import pub
import wx.lib.scrolledpanel as scrolled

#--- jumeg cls
from jumeg.jumeg_base                                     import jumeg_base as jb
#--- jumeg wx stuff
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_frame           import JuMEG_MainFrame
from jumeg.gui.wxlib.jumeg_gui_wxlib_main_panel           import JuMEG_wxMainPanel
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxSplitterWindow,JuMEG_wxCMDButtons,JuMEG_wxControlGrid,JuMEG_wxControlButtons,JuMEG_wxControlButtonPanel
#--- Merger CTRLs
from jumeg.gui.wxlib.jumeg_gui_wxlib_experiment_template  import JuMEG_wxExpTemplate
from jumeg.gui.wxlib.jumeg_gui_wxlib_id_selection_box     import JuMEG_wxIdSelectionBox

from jumeg.gui.utils.jumeg_gui_utils_io                   import JuMEG_UtilsIO_PDFs
#---
from jumeg.gui.wxlib.jumeg_gui_wxlib_pbshost              import JuMEG_wxPBSHosts
from jumeg.gui.jumeg_gui_wx_argparser                     import JuMEG_GUI_wxArgvParser
#---
from jumeg.ioutils.jumeg_ioutils_subprocess               import JuMEG_IoUtils_SubProcess

__version__='2018-09-18.001'


class JuMEG_wxMEEG_PDFBox(wx.Panel):
    """JuMEG MEEG Merger Posted Data File (PDF) Box
    """

    def __init__(self, parent, pdfs=None, title='PDFs', stage=None, bg="grey90", pubsub=True,list=None, **kwargs):
        super(JuMEG_wxMEEG_PDFBox, self).__init__(parent, style=wx.SUNKEN_BORDER)
        self.pubsub        = pubsub
        #self.pubsub_prefix = pubsub_prefix
        self.stage  = stage
        self.pdfs   = pdfs
        self.verbose = False
        self.fmeeg_extention = 'meeg-raw.fif'
        self.meg_list = []
        self.eeg_list = []
        self.title = title
        self._fgs = None
        # ---
        self.__ckbox = {}
        self.__cbbox = {}
        self.__CB_BACK_COLOR = 'white'
        self.__CB_ERROR_COLOR = 'red'

        self.SetBackgroundColour(bg)
        self._wx_init(bg=bg)
        self._ApplyLayout()

    def _wx_init(self, bg="grey80"):
        self.SetBackgroundColour(bg)
        bg1 = "grey90"
        self.pnl_info = wx.Panel(self, style=wx.SUNKEN_BORDER)
        self.pnl_info.SetBackgroundColour(bg1)

        self._pnl_pdf = scrolled.ScrolledPanel(self, -1, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER,
                                               name="PDF_BOX_SCR_PANEL")
        self._pnl_pdf.SetBackgroundColour(bg)

        # --- Label + line
        ds = 4
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        spdf = "{:8} {:14} {:18} {:9} {:10} {:14} {:30} {}".format("MNE", "Id", "Scan", "Date", "Time", "Run", "Raw",
                                                                   "EEG Data")

        hbox.Add(wx.StaticText(self.pnl_info, -1, label=spdf), 1, wx.LEFT | wx.EXPAND | wx.ALL, ds)
        self.pdfinfo_txt = wx.StaticText(self.pnl_info, -1, label="  0 /  0  ")

        stl = wx.BU_EXACTFIT|wx.BU_NOTEXT# | wx.BORDER_NONE
        self._BtDeselect = wx.Button(self.pnl_info,-1,name="PDFBOX.BUTTON.CLEAR",style=stl)
        self._BtDeselect.SetBitmapLabel(wx.ArtProvider.GetBitmap(wx.ART_DELETE, wx.ART_MENU,(12,12)))
        self.Bind(wx.EVT_BUTTON, self.DeselectAll, self._BtDeselect)

        hbox.Add(self.pdfinfo_txt, 0, wx.LEFT | wx.EXPAND | wx.ALL, ds)
        hbox.Add(self._BtDeselect, 0, wx.LEFT | wx.EXPAND | wx.ALL, ds)

        self.pnl_info.SetSizer(hbox)
        self.pnl_info.SetAutoLayout(True)
        self.pnl_info.Fit()

    def _ApplyLayout(self):
        ds = 4
        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.pnl_info, 0, wx.LEFT | wx.EXPAND | wx.ALL)
        self.Sizer.Add(wx.StaticLine(self), 0, wx.LEFT | wx.EXPAND | wx.ALL, ds)
        self.Sizer.Add((0, 0), 0, wx.EXPAND | wx.ALL, ds)
        self.Sizer.Add(self._pnl_pdf, 1, wx.LEFT | wx.EXPAND | wx.ALL, ds)

      # --- add controls
        self.SetAutoLayout(True)
        self.SetSizer(self.Sizer)
        self.Fit()
        self.Update()
        self.Refresh()

    def init_pubsub(self):
        pub.subscribe(self.update,'PDF_BOX.UPDATE')

    def update_ckbox_file_exist(self,ckbox,f):
        if os.path.isfile(f.partition('-')[0] +','+ self.fmeeg_extention):
           ckbox.SetForegroundColour(wx.BLUE)
           ckbox.SetValue(False)

    def update(self, pdfs=None,n_pdfs=None,reset=False):

        if isinstance(pdfs, (dict)):
            self.pdfs = pdfs
        size_orig = self.GetSize()
      # --- clear pdf panel
        self.reset()

        if reset:
           if self.pdfs:
              self.pdfs['mne']=[]
              self.pdfs['eeg']=[]
        else:
           n_subjects = len(self.pdfs['mne'])
           ds = 5
           LEA = wx.LEFT | wx.EXPAND | wx.ALL
           fgs1 = wx.FlexGridSizer(n_pdfs + n_subjects, 2, ds, ds)
           fgs1.AddGrowableCol(1, proportion=2)

           for subject_id in self.pdfs['mne']:
               fidx = 0
               self.__ckbox[subject_id] = []
               self.__cbbox[subject_id] = []

               for f in sorted(self.pdfs['mne'][subject_id]['raw']):
                   if subject_id not in (self.pdfs['eeg']): continue

                   pdf = os.path.basename(f)
                 # --- init  mne checkbox
                   spdf = "{:7} {:10} {:8} {:14} {:10} {:10}".format(*pdf.split("_"))

                   ckb = wx.CheckBox(self._pnl_pdf, wx.NewId(), label=spdf, name=subject_id + '_' + str(fidx))
                   ckb.SetValue(True)
                   ckb.SetForegroundColour(wx.BLACK)
                   ckb.SetToolTip(wx.ToolTip(self.pdfs['mne'][subject_id]["path"][fidx]))

                   self.update_ckbox_file_exist(ckb,self.pdfs['mne'][subject_id]["path"][fidx]+ '/' + pdf)
                   fgs1.Add(ckb)

                # --- init eeg file selectioncombobox
                   cbb = wx.ComboBox(self._pnl_pdf, wx.NewId(), choices=[''], style=wx.CB_READONLY | wx.CB_SORT)
                   cbb.SetItems(self.pdfs['eeg'][subject_id]['raw'])  # will clear cbb first
                   cbb.SetName(subject_id + '_' + str(fidx))
                # --- if eeg vhdr exist
                   if self.pdfs["mne"][subject_id]['eeg_idx'][fidx] > -1:
                      eeg_idx = self.pdfs["mne"][subject_id]['eeg_idx'][fidx]
                      cbb.SetValue(self.pdfs['eeg'][subject_id]['raw'][eeg_idx])
                      cbb.SetToolTip(wx.ToolTip(self.pdfs['eeg'][subject_id]["path"][eeg_idx]))
                      cbb.SetBackgroundColour(self.__CB_BACK_COLOR)

                # ToDo update ToolTip path if OnSelection
                # except:
                   else:
                      ckb.SetValue(False)

                   fgs1.Add(cbb, 0, LEA, ds + 1)
                   ckb.Bind(wx.EVT_CHECKBOX, self._ClickOnCkBox)
                   cbb.Bind(wx.EVT_COMBOBOX, self._ClickOnCombo)

                   self.__ckbox[subject_id].append(ckb)
                   self.__cbbox[subject_id].append(cbb)

                   fidx += 1

               fgs1.Add(wx.StaticLine(self._pnl_pdf), 0, wx.LEFT | wx.EXPAND | wx.ALL)
               fgs1.Add(wx.StaticLine(self._pnl_pdf), 0, wx.LEFT | wx.EXPAND | wx.ALL)

            # ---

           self._pnl_pdf.SetSizer(fgs1)
           fgs1.Fit(self._pnl_pdf)

        self._pnl_pdf.SetAutoLayout(1)
        self._pnl_pdf.SetupScrolling()
        self._pnl_pdf.FitInside()

        self.Fit()
        self.SetSize(size_orig)
        self.Update()
        self.Refresh()
        self.__update_pdfinfo()

    def DeselectAll(self):
        print("PDFBox click on DeselectAll")

    def _ClickOnCkBox(self, evt):
        obj = evt.GetEventObject()
        n = obj.GetName()

        if obj.GetValue():
           combo = self.__find_obj_by_name(self.__cbbox, n)
           if combo:
              if combo.GetValue():
                 obj.SetValue(True)
              else:
                 obj.SetValue(False)

        self.__update_pdfinfo()

    def _ClickOnCombo(self, evt):
        obj = evt.GetEventObject()
        n = obj.GetName()
        ckbt = self.__find_obj_by_name(self.__ckbox, n)
        if ckbt:
            if obj.GetValue():
                ckbt.SetValue(True)
            else:
                ckbt.SetValue(False)
            self.__update_pdfinfo()

            # --- ck for if eeg file is multi selected
            # --- https://stackoverflow.com/questions/11528078/determining-duplicate-values-in-an-array
            subject_id = n.split('_')[0]
            a = []
            # --- fill array with selected index
            for cb in self.__cbbox[subject_id]:
                cb.SetBackgroundColour(self.__CB_BACK_COLOR)
                a.append(cb.GetSelection())
            # --- ck for unique
            uitem = np.unique(a)
            # --- exclude zeros == deselected files
            for i in uitem:
                # if i < 1: continue
                double_idx = np.where(a == i)[0]
                if double_idx.shape[0] < 2: continue  # no double selection
                for idx in double_idx:
                    if self.__cbbox[subject_id][idx].GetValue():
                        self.__cbbox[subject_id][idx].SetBackgroundColour(self.__CB_ERROR_COLOR)

    def __find_obj_by_name(self, obj, n):
        # https://stackoverflow.com/questions/653509/breaking-out-of-nested-loops
        # ckbt = next(( x for x in self.__ckbox if x.GetName() == n), None)
        for item in obj:
            for x in obj[item]:
                if x.GetName() == n:
                    return x

    def __update_pdfinfo(self):
        """"""
        sel = 0
        n_ck = 0
        for item in (self.__ckbox):
            for ck in (self.__ckbox[item]):
                sel += int(ck.GetValue())
                n_ck += 1
        spdf = "{:3d} / {:3d}".format(sel, n_ck)
        self.pdfinfo_txt.SetLabel(spdf)

    def reset(self):
        """"""
        for child in self._pnl_pdf.GetChildren():
            child.Destroy()

        self.__cbbox = {}
        self.__ckbox = {}
        # self._pnl_pdf.SetSize(s)
        self.Layout()
        self.Fit()
        self.Refresh()

    def GetPDFs(self):
        """
        get the posted data files

        Results
        -------
         list of pdf structure
         [ { mne:{path:mne-path,file:xyz.fif},
             eeg:{path:eeg-path,file:xyz.vhdr}
            },...]
        """
        flist = []
        for item in (self.__ckbox):
            mne_idx = 0
            for ck in (self.__ckbox[item]):
                if ck.GetValue():
                    eeg_idx = self.__cbbox[item][mne_idx].GetSelection()  # first item is "" empty
                    flist.append(
                        {"mne": {"path": self.pdfs['mne'][item]["path"][mne_idx],
                                 "file": self.pdfs['mne'][item]['raw'][mne_idx]},
                         "eeg": {"path": self.pdfs['eeg'][item]["path"][eeg_idx],
                                 "file": self.pdfs['eeg'][item]['raw'][eeg_idx]}
                         })

                mne_idx += 1

            if self.verbose:
                wx.LogMessage( jb._pp.pformat(flist))# , head="MEEG posted PDFs")
        return flist

class JuMEG_wxMEEGMergerPanel(JuMEG_wxMainPanel):
      """
      """
      def __init__(self, parent,**kwargs):
          super().__init__(parent,name="JUMEG_MEEG_MERGER_PANEL")

          self.module_path      = os.getenv("JUMEG_PATH") + "/jumeg/"
          self.module_name      = "jumeg_merge_meeg"
          self.module_extention = ".py"
          self.SubProcess       = JuMEG_IoUtils_SubProcess()
          self._init(**kwargs)

      @property
      def fullfile(self): return self.module_path+"/"+self.module_name+ self.module_extention

      def update(self,**kwargs):
          self.stage  = kwargs.get("stage", os.getenv("JUMEG_PATH", os.getcwd()) + "/jumeg/" )
          self.module = kwargs.get("module","jumeg_merge_meeg")
          self.PDFs   = JuMEG_UtilsIO_PDFs()

         #-- update wx CTRLs
          self.PanelA.SetTitle(v="PDF`s")
          self.PanelB.SetTitle(v="Parameter")
         #---
          ds=1
          LEA = wx.ALIGN_LEFT | wx.EXPAND | wx.ALL

         #-- Top
          self.ExpTemplate = JuMEG_wxExpTemplate(self.TopPanel)
          self.HostCtrl    = JuMEG_wxPBSHosts(self.TopPanel, prefix=self.GetName())
          self.TopPanel.GetSizer().Add(self.ExpTemplate,3,LEA,ds)
          self.TopPanel.GetSizer().Add(self.HostCtrl,1, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL,ds)
         #--- A IDs;PDFs
          self.IdSelectionBox = JuMEG_wxIdSelectionBox(self.PanelA.Panel, title='IDs')#, **kwargs)
          self.PDFBox         = JuMEG_wxMEEG_PDFBox(self.PanelA.Panel, **kwargs)
          self.PanelA.Panel.GetSizer().Add(self.IdSelectionBox, 0, LEA,ds)
          self.PanelA.Panel.GetSizer().Add(self.PDFBox, 1, LEA, ds)
         # --- B  right
          self.AP = JuMEG_GUI_wxArgvParser(self.PanelB.Panel, use_pubsub=self.use_pubsub, fullfile=self.fullfile,
                                           module=self.module_name, ShowParameter=True)
          self.PanelB.Panel.GetSizer().Add(self.AP, 1, LEA,ds)
         #---
          self.Bind(wx.EVT_BUTTON, self.ClickOnButton)

      def _update_hosts(self):
          pass

      def ClickOnExperimentTemplateUpdate(self,stage=None,scan=None,data_type=None):
          """
          call IdSelectionBox.update and update ID listbox
          reset PDFs for new selection

          Parameter
          ---------
           stage:     stage / path to data
           scan:      name of scan
           data_type: mne / eeg
          """
          self.IdSelectionBox.update(stage=stage,scan=scan,data_type=data_type)
          self.PDFBox.update(reset=True)

      def init_pubsub(self, **kwargs):
          """ init pubsub call overwrite """
          pub.subscribe(self.ClickOnApply,self.GetName().upper()+".BT_APPLY")
          pub.subscribe(self.ClickOnExperimentTemplateUpdate,'EXPERIMENT_TEMPLATE.UPDATE')
    #---
      def Cancel(self):
          wx.LogMessage("CLICK ON CANCEL")
          pub.sendMessage("SUBPROCESS.CANCEL",verbose=self.verbose)

      def ClickOnApply(self):
          """
          apply to subprocess

          """
          self.PDFBox.verbose = self.verbose
          cmd_parameter       = self.AP.GetParameter()
          joblist=[]

          for pdf in self.PDFBox.GetPDFs():
              cmd = os.path.basename(self.fullfile)
              cmd += " -smeg " + pdf["mne"]["path"]
              cmd += " -fmeg " + pdf["mne"]["file"]
              cmd += " -seeg " + pdf["eeg"]["path"]
              cmd += " -feeg " + pdf["eeg"]["file"]
              cmd += " "+ cmd_parameter
              joblist.append( cmd )

          if self.verbose:
             wx.LogMessage(jb.pp_list2str(joblist, head="MEEG Merger Job list: "))
             wx.LogMessage(jb.pp_list2str(self.HostCtrl.HOST.GetHostInfo(),head="HOST Info"))
          pub.sendMessage("SUBPROCESS.RUN.START",joblist=joblist,hostinfo=self.HostCtrl.HOST.GetHostInfo(),verbose=self.verbose)

      def ClickOnButton(self, evt):
          obj = evt.GetEventObject()
          if obj.GetName().startswith("ID_SELECTION_BOX.UPDATE"):
             self.PDFs.stage = self.ExpTemplate.stage
             self.PDFs.scan  = self.ExpTemplate.scan

             self.PDFs.update(id_list=self.IdSelectionBox.ItemSelectedList)
             self.PDFBox.update(pdfs=self.PDFs.pdfs, n_pdfs=self.PDFs.number_of_pdfs_mne)

          if obj.Label == "CLOSE":
             pub.sendMessage('MAIN_FRAME.CLICK_ON_CLOSE',evt=evt)
          if obj.Label == "CANCEL":
             pub.sendMessage('MAIN_FRAME.CLICK_ON_CANCEL',evt=evt)
          if obj.Label == "APPLY":
             self.ClickOnApply()
          else:
             evt.Skip()


class JuMEG_GUI_MEEGMergeFrame(JuMEG_MainFrame):
    def __init__(self,parent,id,title,pos=wx.DefaultPosition,size=[1024,768],name='JuMEG MEEG Merger INM4-MEG-FZJ',*kargs,**kwargs):
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
        return JuMEG_wxMEEGMergerPanel(self,name="JuMEG_TEST_PANEL_OOOO",**kwargs)
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
   frame = JuMEG_GUI_MEEGMergeFrame(None,-1,'JuMEG MEEG MERGER',module="jumeg_merge_meeg",function="get_args",ShowLogger=True,ShowParameter=True,debug=True,verbose=True)
   #frame = JuMEG_GUI_MEEGMergerFrame(None,-1,'JuMEG MEEG MERGER FZJ-INM4',debug=True,verbose=True,ShowLogger=True)
   app.MainLoop()
