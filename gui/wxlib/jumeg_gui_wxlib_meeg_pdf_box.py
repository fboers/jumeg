#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 24 08:17:37 2018

@author: fboers
"""
import os
import wx
import wx.lib.scrolledpanel as scrolled

__version__="v2018-07-11-001"

class JuMEG_wxMEEG_SelectionBox(scrolled.ScrolledPanel):
    def __init__(self, parent):
        scrolled.ScrolledPanel.__init__(self, parent, -1)
        self.__obj = []
        self._fsg = None
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.vbox)
        self.SetAutoLayout(True)
        self.SetupScrolling()
     
    def update(self,flist):
        """
        ck bt, id ,scan session ,run ,fname  # eeg combo eeg vhdr
        meg path # eeg path
        
        """
      
        self._clear()
        
        empty_cell=(0,0)
        ds   = 5
        LEA = wx.LEFT|wx.EXPAND|wx.ALL
        self._fgs = wx.FlexGridSizer(len(flist),8,ds,ds)
        for f in flist:
            pdf  = os.path.basename(f)
           # path = os.path.dirname(f)
        
            id,scan,date,time,run,fname = pdf.split("_")
  
            self.__obj.append( wx.CheckBox(self._pnl_pdf,wx.NewId()) )  
            self.__obj[-1].SetValue(True)
            self._fgs.Add(self.__obj[-1],0,LEA,ds)
       
            self.__obj.append( wx.StaticText(self._pnl_pdf,wx.NewId(),label=id ) )  
            self._fgs.Add(self.__obj[-1],0,LEA,ds)
       
            self.__obj.append( wx.StaticText(self._pnl_pdf,wx.NewId(),label=scan ) )  
            self._fgs1.Add(self.__obj[-1],0,LEA,ds)
        
            self.__obj.append( wx.StaticText(self._pnl_pdf,wx.NewId(),label=date+"-"+time ) )  
            self._fsg.Add(self.__obj[-1],0,LEA,ds)
       
            self.__obj.append( wx.StaticText(self._pnl_pdf,wx.NewId(),label=run ) )  
            self._fgs.Add(self.__obj[-1],0,LEA,ds)
       
            self.__obj.append( wx.StaticText(self._pnl_pdf,wx.NewId(),label=fname ) )  
            self._fgs.Add(self.__obj[-1],0,LEA,ds)
        
            self._fgs.Add(empty_cell,0,LEA,ds) # skip min bt
       
            self.__obj.append( wx.ComboBox(self._pnl_pdf,wx.NewId(),choices=["A","B","C"] ) ) 
            self._fgs.Add(self.__obj[-1],1,LEA,ds)
       
        self._pnl_pdf.SetSizer( self._fgs )
        self._pnl_pdf.SetAutoLayout(1)
        self._pnl_pdf.SetupScrolling()

        
        #vbox.Add(fgs1,1, wx.LEFT|wx.EXPAND|wx.ALL,ds)  
    def _clear(self):
        """"""
        
        for child in self._pnl_pdf.GetChildren():
            child.Destroy()
        
        if self._fsg:
           self._fsg.Destroy()
         
        """    
        children = self._pnl_pdf.GetChildren()
 
        for child in children:
            widget = child.GetWindow()
            print widget
            if isinstance(widget, wx.TextCtrl):
                widget.Hide()
                widget.Clear()
        """  
        self.__obj = []      
        self.Layout()
        self.Fit()      
    

"""

   def pdf_panel(self,flist):
   
        
  
        sb = wx.StaticBox(self, label="PDFs")
        vbox = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.__obj = []
        
        empty_cell=(0,0)
       # hbox=wx.BoxSizer(wx.HORIZONTAL)
        ds   = 5
        fgs1 = wx.FlexGridSizer(len(flist),8,ds,ds)
        for f in flist:
            pdf  = os.path.basename(f)
            path = os.path.dirname(f)
        
            id,scan,date,time,run,fname = pdf.split("_")
  
            self.__obj.append( wx.CheckBox(self,wx.NewId()) )  
            self.__obj[-1].SetValue(True)
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
       
            self.__obj.append( wx.StaticText(self,wx.NewId(),label=id ) )  
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
       
            self.__obj.append( wx.StaticText(self,wx.NewId(),label=scan ) )  
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
        
            self.__obj.append( wx.StaticText(self,wx.NewId(),label=date+"-"+time ) )  
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
       
            self.__obj.append( wx.StaticText(self,wx.NewId(),label=run ) )  
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
       
            self.__obj.append( wx.StaticText(self,wx.NewId(),label=fname ) )  
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
        
            fgs1.Add(empty_cell,0,wx.LEFT|wx.EXPAND,ds) # skip min bt
       
            self.__obj.append( wx.ComboBox(self,wx.NewId(),choices=["A","B","C"] ) ) 
            fgs1.Add(self.__obj[-1],0,wx.LEFT|wx.EXPAND,ds)
        
        vbox.Add(fgs1,1, wx.LEFT|wx.EXPAND|wx.ALL,ds)  
        return vbox
        
        """
     