import psutil # http://code.google.com/p/psutil/
import wx
from ObjectListView import ObjectListView, ColumnDefn

########################################################################
class Process(object):
    """ """

    #----------------------------------------------------------------------
    def __init__(self, name, pid, exe, user, cpu, mem, desc=None):
        """Constructor"""
        self.name = name
        self.pid = pid
        self.exe = exe
        self.user = user
        self.cpu = cpu
        self.mem = mem
        #self.desc = desc
        
########################################################################
class MainPanel(wx.Panel):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.procs = []
        
        self.procmonOlv = ObjectListView(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.setProcs()
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.procmonOlv, 1, wx.EXPAND|wx.ALL, 5)
        self.SetSizer(mainSizer)
        self.updateDisplay()
        
        # check for updates every 5 seconds
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.timer.Start(5000)
        
    #----------------------------------------------------------------------
    def setProcs(self):
        """"""
        cols = [
            ColumnDefn("name", "left", 150, "name"),
            ColumnDefn("pid", "left", 50, "pid"),
            ColumnDefn("exe location", "left", 100, "exe"),
            ColumnDefn("username", "left", 75, "user"),
            ColumnDefn("cpu", "left", 75, "cpu"),
            ColumnDefn("mem", "left", 75, "mem"),
            #ColumnDefn("description", "left", 200, "desc")
            ]
        self.procmonOlv.SetColumns(cols)
        self.procmonOlv.SetObjects(self.procs)
        
    #----------------------------------------------------------------------
    def update(self, event):
        """"""
        self.updateDisplay()
        
    #----------------------------------------------------------------------
    def updateDisplay(self):
        """"""
        pids = psutil.get_pid_list()
        for pid in pids:
            
            try:
                p = psutil.Process(pid)
                new_proc = Process(p.name,
                                   str(p.pid),
                                   p.exe,
                                   p.username,
                                   str(p.get_cpu_percent()),
                                   str(p.get_memory_percent())
                                   )
                self.procs.append(new_proc)
            except:
                pass
            
        self.setProcs()
    
########################################################################
class MainFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="PyProcMon")
        panel = MainPanel(self)
        self.Show()
        
if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
    