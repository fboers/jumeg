import sys,os
import wx

from jumeg.tsvgl.wxutils.jumeg_tsv_wx_dlg_subplot import TSVSubPlotDialog
from jumeg.tsvgl.wxutils.jumeg_tsv_wx_dlg_group   import TSVGroupDialog

#try:
#    from agw import floatspin as FS
#except ImportError: # if it's not there locally, try the wxPython lib.
#    import wx.lib.agw.floatspin as FS

"""
 self.mvp[:,0] = dborder
          if (self.opt.plot.cols >1):      
             mat = np.zeros( (self.opt.plot.rows,self.opt.plot.cols) )
             mat += np.arange(self.opt.plot.cols)
             self.mvp[:,0] +=  mat.T.flatten() * ( dw + 2 *dborder)          
"""           

def jumeg_wx_dlg_group(opt=None):
    dlg = TSVGroupDialog(title="JuMEG TSV Groups Option",opt=opt)
   # opt.info()
    if dlg.ShowModal() == wx.ID_OK:
       dlg.Destroy()
       #print"TEST GRP DLG"
       #print opt
       #import pprint
       # pprint.pprint(opt)
       opt.info()
       return opt
    else:
       opt.info()
       return None
         
def jumeg_wx_dlg_subplot(opt=None):
        
    dlg = TSVSubPlotDialog(title="JuMEG TSV Plot Option",opt=opt)
    if dlg.ShowModal() == wx.ID_OK:
       dlg.Destroy()
       # return dlg.Destroy()
       return opt
    else:
       return None
       
    
def jumeg_wx_openfile(w,path=None):

    fout     = None
    wildcard = "FIF files (*.fif)|*.fif|All files (*.*)|*.*"

    if path is None:
       path = os.getcwd()

   # dlg = wx.FileDialog(w, "Choose a file", path, "","FIF (*.fif)|*.fif", wx.FD_OPEN| wx.FD_FILE_MUST_EXIST|wx.CHANGE_DIR)
    dlg = wx.FileDialog(w, "Choose a file", path,wildcard=wildcard,style=wx.FD_OPEN| wx.FD_FILE_MUST_EXIST|wx.CHANGE_DIR)

    if dlg.ShowModal() == wx.ID_OK:
       fout = dlg.GetPath()
       print"DLG: " + fout
    dlg.Destroy()
    return fout

def jumeg_wx_opendir(w):
         dlg = wx.DirDialog(w, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
         if dlg.ShowModal() == wx.ID_OK:
             dlg_path = dlg.GetPath()
         dlg.Destroy()
         return dlg_path

def MsgDlg(w, string, caption = "JuMEG TSV", style=wx.YES_NO|wx.CANCEL):
    """Common MessageDialog."""
    dlg = wx.MessageDialog(w, string, caption, style)
    result = dlg.ShowModal()
    dlg.Destroy()
    return result

