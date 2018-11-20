import sys
import numpy as np

import wx

# from python praxis book 
# import wx.lib.newevent s 1076
# from threading import Thread s1078


#from jumeg.jumeg_base               import JuMEG_Base_Basic
#from jumeg.tsv.jumeg_tsv_plot2d_wx  import JuMEG_TSV_Plot2D

#import jumeg.tsv.jumeg_tsv_wx_utils as jwx_utils
#from jumeg.tsv.jumeg_tsv_data import JuMEG_TSV_DATA

from jumeg.tsvgl.io.jumeg_tsv_io_data                 import JuMEG_TSV_IO_DATA
#from jumeg.tsvgl.plot2d.jumeg_tsv_plot2d_wx_gl_canvas import JuMEG_TSV_PLOT2D_PANEL
from jumeg.tsvgl.plot2d.jumeg_tsv_wx_plot2d import JuMEG_TSV_PLOT2D_PANEL

import jumeg.tsvgl.wxutils.jumeg_tsv_wx_utils as jwx_utils
#from   jumeg.tsv.wxutils.jumeg_tsv_wx_dlg_group import TSVGroupDialog
#from jumeg.tsv.test.axis01 import JuMEG_TSV_AXIS

#----------------------------------------------------------------------------
class JuMEG_TSV_Plot2DPanel(JuMEG_TSV_PLOT2D_PANEL):
      def __init__(self, parent):
          super(JuMEG_TSV_Plot2DPanel,self).__init__(parent)
          
          self._verbose=False
          
         # __metaclass__= JuMEG_TSV_Plot2D(self)
          
         
         # self.ruler = rc.RulerCtrl(self, orient=wx.HORIZONTAL)
         # self.ruler.SetRange(0.0,1.0)
         # self.ruler.AddIndicator(id=100, value=0.0)
         # self.ruler.AddIndicator(id=101, value=6.5)
        #  self.ruler.Bind(rc.EVT_INDICATOR_CHANGED, self.onIndicator)
            
          self.SetBackgroundColour("yellow")
          
       
          #self._Plot2D = JuMEG_TSV_PLOT2D_PANEL(self)
          #self._Plot2D.SetMinSize((200,150 ))
          
          #vbox = wx.BoxSizer(wx.VERTICAL)         
          #vbox.Add(self._Plot2D, 1,wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,4)
          #self.SetAutoLayout(True)
          #self.SetSizer(vbox)
          self.SetAutoLayout(True)
          
#--- return the wx canvas
      def __get_plot2d_canvas(self):
          return self.Plot2DCanvas
      plot_window = property(__get_plot2d_canvas)    
      
      
      def __get_verbose(self):
          return self.__verbose
      def __set_verbose(self,v):
          self.__verbose = v
          self.plot_window.opt.verbose = v
      verbose = property(__get_verbose,__set_verbose)    
           
      
      def __get_plot_option(self):
          return self.plot_window.option
      def __set_plot_option(self,opt):
          self.plot_window.option = opt
      option = property(__get_plot_option,__set_plot_option)    
     
      def __get_plot_info(self):
          return self.plot_window.info
      def __set_plot_info(self,info):
          self.plot_window.info = info
          #self.plot_window.data_channel_selection_is_update = False
         #--- update e.g. channel selction
          self.plot_window.info.update()        
      info = property(__get_plot_info,__set_plot_info)    

     #---
      def change_subplot_option(self,raw_is_loaded=False):
        
          self.plot_window.is_on_draw = True           
          opt = jwx_utils.jumeg_wx_dlg_subplot(opt=self.option)
          self.plot_window.is_on_draw=False       
          if opt:
             self.option = opt
             if raw_is_loaded:
                self.plot_window.update()

      def change_group_option(self,raw_is_loaded=False):
      
          self.plot_window.is_on_draw = True           
          info = jwx_utils.jumeg_wx_dlg_group(opt=self.info)
          self.plot_window.is_on_draw = False       
          if info:
             self.info = info
             if raw_is_loaded:
                self.update()
                
      def update(self,raw,channels2plot=None,cols=None):
          self.plot_window.update(raw=raw,channels2plot=channels2plot,cols=cols)          

              
#----------------------------------------------------------------------------
class JuMEG_TSV_Frame(wx.Frame):

      def __init__(self,parent,id,title, pos=wx.DefaultPosition,size=wx.DefaultSize,name='main_frame',**kwargs):
          style = wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE
          super(JuMEG_TSV_Frame, self).__init__(parent, id, title, pos, size, style, name)
          
          self.verbose    = kwargs['verbose']
          self.debug      = kwargs['debug']
          self.n_channels = kwargs['n_channels']
          self.n_cols     = kwargs['n_cols']
         
      
          self.TSV_DATA = JuMEG_TSV_IO_DATA(fname=kwargs['fname'],path=kwargs['path'],
                                            bads=kwargs['bads'],experiment=kwargs['experiment'])
      
          self.OnInit()
          self.ApplyLayout()
          self.update_data(channels2plot=self.n_channels,cols=self.n_cols)

      def OnInit(self):

          self.main_panel = wx.Panel(self,-1)
          self.main_panel.SetBackgroundColour("green")
         

          self.wx_InitStatusbar()
          #self.wx_init_toolbar()
          self.wx_InitMainMenu()

          #self.Bind(wx.EVT_CLOSE,   self.OnCloseWindow)
          self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)


         # vbox.Add(self.main_panel, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,5)

          #self.Plot2DPanel = JuMEG_TSV_Plot2DPanel(self)
          #vbox.Add(self.Plot2DPanel, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,1)
          #self.SetAutoLayout(True)
          #self.SetSizer(vbox)

          #self.plt2d.option.plot_cols         = self.n_cols 
          #self.plt2d.plot.raw = self.TSV_DATA

          
         # self.SetTopWindow(self.frame)
         
        
         #---
          
          self.Plot2DPanel = JuMEG_TSV_PLOT2D_PANEL(self) #JuMEG_TSV_Plot2DPanel(self)
         # self.Show(True)
         # self.SetSize((640,480))
          #self.SetTopWindow(self)
         
         
         # vbox.Add(self.Plot2DPanel, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,1)
         # self.SetAutoLayout(True)
         # self.SetSizer(vbox)
          
          
         # self.SetFocus()


          return True

      def ApplayLayout(self):
          self.SetSize((640,480))
          vbox = wx.BoxSizer(wx.VERTICAL)     
          vbox.Add(self.Plot2DPanel, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,1)
          
          self.SetAutoLayout(True)
          self.SetSizer(vbox)
          self.Show(True)
          self.Layout()
    

      def __menu_data(self):
          return (("&File",
                  ("&Open", "Open in status bar",wx.ITEM_NORMAL, self.ClickOnOpen),
                  ("&Save", "Save", wx.ITEM_NORMAL,self.ClickOnSave),
                  ("", "", "",""),
                  ("&Clear", "Clear", wx.ITEM_NORMAL,self.ClickOnClear),
                  ("", "", "",""),
                  ("&Exit", "Exit", wx.ITEM_NORMAL,self.ClickOnExit)),
                  ("&Option",
                  ("&Plot","Subplot",wx.ITEM_NORMAL,self.ClickOnPlotSubplot),
                  ("&Groups","Group",wx.ITEM_NORMAL,self.ClickOnPlotGroup)),

                  ("&Settings",
                  ("&StatusBar","Statusbar On/Off", wx.ITEM_CHECK,self.ToggleStatusBar,True),
                  ("", "", "",""),
                  ("&Verbose","Verbose",wx.ITEM_CHECK,self.ToggleVerbose,self.verbose),
                  ("&Debug","Debug",wx.ITEM_CHECK,self.ToggleDebug,self.debug)),

                  ("&About",
                  ("&About", "About", wx.ITEM_NORMAL,self.ClickOnAbout)))


      def wx_InitMainMenu(self):

          menuBar = wx.MenuBar()

          for eachMenuData in self.__menu_data():
              menuLabel = eachMenuData[0]
              menuItems = eachMenuData[1:]
              menuBar.Append(self.createMenu(menuItems), menuLabel)
          self.SetMenuBar(menuBar)

      def createMenu(self, md):
          '''
          input: sub menu list 
                 label,status,kind,handler [True/False for kind]
          e.g.:
               ("&Open", "Open in status bar",wx.ITEM_NORMAL, self.ClickOnOpen)
               or as checkbox
               ("&StatusBar","Statusbar On/Off", wx.ITEM_CHECK,self.ToggleStatusBar,True)
           
          '''
          menu = wx.Menu()
          for msub in md:
             # for label,status,k,handler in sub_menu[0:3]:
              if not msub[0]:
                 menu.AppendSeparator()
                 continue
            
              menuItem = menu.Append(wx.ID_ANY,msub[0],msub[1],kind=msub[2])
              if (msub[2] == wx.ITEM_CHECK):
                 menu.Check(menuItem.GetId(),msub[-1] )
              self.Bind(wx.EVT_MENU,msub[3], menuItem)

          return menu

     # def __ApplyLayout(self):
     #     """Layout the panel"""
     #     vbox = wx.BoxSizer(wx.VERTICAL)
     #     vbox.Add(self._ctrl_subplot, 0,flag=wx.ALL|wx.EXPAND, border=10)  
     #     vbox.Add(self._ctrl_time, 0,flag=wx.ALL|wx.EXPAND, border=10)
     #     vbox.Add(self._btbox,0,wx.EXPAND,border=5)
     #   
     #     self.SetSizerAndFit(vbox)
          #self.SetAutoLayout(True)
    
#--- init stuff  I/O


#--- data update
      def update_data(self,fname=None,channels2plot=None,cols=None):
          
          self.TSV_DATA.update(fname=fname)
          if self.TSV_DATA.raw_is_loaded:
             self.Plot2DPanel.update(self.TSV_DATA.raw,channels2plot=channels2plot,cols=cols)
             #self.plt2d.test_axis.range_max=self.plt2d.plot.xmax
             #self.plt2d.test_axis.range_min=self.plt2d.plot.xmin
             #self.plt2d.test_axis.Refresh()
             
             self.SetTitle('JuMEG-TSV: '+self.TSV_DATA.fname)
                   
#--- click on stuff

      def ClickOnOpen(self,event=None):

          f = jwx_utils.jumeg_wx_openfile(self,path=self.TSV_DATA.path)
          if f:
             self.update_data(fname=f)
            

      def ClickOnSave(self,event=None):
          print"click_on_save"

      def ClickOnClear(self,event=None):
          print"click_on_clear"

      def ClickOnExit(self,event=None):
         # msg = wx.MessageDialog('Are you sure to quit?', 'Question',wx.YES_NO | wx.NO_DEFAULT, self.frame)
          dlg = wx.MessageDialog(self.frame, 'Are you sure to quit?', 'Question', wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
          
          if (dlg.ShowModal() == wx.ID_YES):
             self.Close(True)
            # wx.Exit()
             

#---TODO self.plt2d.plot... as short cut; self.plt2d.plot._is_on_draw-> property

      def ClickOnPlotSubplot(self,event=None):
          self.plt2d.change_subplot_option(raw_is_loaded=self.TSV_DATA.raw_is_loaded)

      def ClickOnPlotGroup(self,evt=None):
          self.plt2d.change_group_option(raw_is_loaded=self.TSV_DATA.raw_is_loaded)
                
    
     # def ClickOnChannelsOpt(self,event=None):
     #     print"click_on_channels"

      def ClickOnAbout(self,event=None):
          jwx_utils.jumeg_wx_utils_about_box()


      def wx_InitStatusbar(self):
          self.statusbar = self.CreateStatusBar(3)
         # self.statusbar.SetStatusWidths([-1, -1 , -1])
          #self.statusbar.SetStatusText('1', '2')


# statusbar_fields = [("ButtonPanel wxPython Demo, Andrea Gavana @ 02 Oct 2006"),
#                            ("Welcome To wxPython!")]

#        for i in range(len(statusbar_fields)):
#            self.statusbar.SetStatusText(statusbar_fields[i], i)


      def OnExitApp(self, evt):
          self.Close(True)

      #def OnCloseWindow(self, evt):
          print "ClickOnCloseWindow"
         # if hasattr(self, "window") and hasattr(self.window, "ShutdownDemo"):
         #    self.window.ShutdownDemo()
         # evt.Skip()

      def OnKeyDown(self, e): 

          key = e.GetKeyCode()
          #print"EVT OnKeyDown: " + key
        #---escape to quit
          if key == wx.WXK_ESCAPE:
             self.ClickOnExit(e)
          e.Skip()


      def ToggleStatusBar(self, evt):
        
          if self.__ischecked(evt):
             self.statusbar.Show()
          else:
             self.statusbar.Hide()
      
      
      def ToggleVerbose(self, evt):
        
          if self.__ischecked(evt) :
             self.verbose=True
          else:
             self.verbose=False
             
          self.plt2d.verbose=self.verbose   
      
      def ToggleDebug(self, evt):
        
          if self.__ischecked(evt) :
             self.debug=True
          else:
             self.debug=False


      def __ischecked(self,evt):
         
          menu = evt.GetEventObject()
          menuItem = menu.FindItemById( evt.GetId() )
          return menuItem.IsChecked()


      
#-------------------------------------------------------------------------
# fname=opt.fname,path=opt.path,verbose=opt.v,debug=opt.d,experiment=opt.exp,
# duration=opt.duration,start=opt.start,n_channels=opt.n_channels,bads=opt.bads
def jumeg_tsv_gui(**kwargs):
    app = wx.App()
   # redirect stout/err to wx console
   # wx.App.__init__(self,redirect=False, filename=None)
    frame = JuMEG_TSV_Frame(None,-1,'JuMEG Time Series Viewer',**kwargs)
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
   jumeg_tsv_gui(**kwargs)

