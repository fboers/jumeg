import controller
import psutil # http://code.google.com/p/psutil/
import wx

from ObjectListView import ObjectListView, ColumnDefn
#from wx.lib.pubsub import Publisher
from wx.lib.pubsub import pub
########################################################################
class MainPanel(wx.Panel):
    """"""

    #----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent)
        self.currentSelection = None
        self.gui_shown = False
        self.procs = []
        self.sort_col = 0
        
        self.col_w = {"name":175,
                      "pid":50,
                      "exe":300,
                      "user":175,
                      "cpu":60,
                      "mem":75}
                
        self.procmonOlv = ObjectListView(self, style=wx.LC_REPORT|wx.SUNKEN_BORDER)
        self.procmonOlv.Bind(wx.EVT_LIST_COL_CLICK, self.onColClick)
        self.procmonOlv.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onSelect)
        #self.procmonOlv.Select
        self.setProcs()
        
        endProcBtn = wx.Button(self, label="End Process")
        endProcBtn.Bind(wx.EVT_BUTTON, self.onKillProc)
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.procmonOlv, 1, wx.EXPAND|wx.ALL, 5)
        mainSizer.Add(endProcBtn, 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.SetSizer(mainSizer)
        
        # check for updates every 15 seconds
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.update("")
        self.setProcs()
        
        # create a pubsub receiver
        pub.subscribe(self.updateDisplay, "update")
        
    #----------------------------------------------------------------------
    def onColClick(self, event):
        """
        Remember which column to sort by, currently only does ascending
        """
        self.sort_col = event.GetColumn()
        
    #----------------------------------------------------------------------
    def onKillProc(self, event):
        """
        Kill the selected process by pid
        """
        obj = self.procmonOlv.GetSelectedObject()
        print
        pid = int(obj.pid)
        try:
            p = psutil.Process(pid)
            p.terminate()
            self.update("")
        except Exception, e:
            print "Error: " + e
            
    #----------------------------------------------------------------------
    def onSelect(self, event):
        """
        Gets called when an item is selected and helps keep track of 
        what item is selected
        """
        item = event.GetItem()
        itemId = item.GetId()
        self.currentSelection = itemId
        
    #----------------------------------------------------------------------
    def setProcs(self):
        """
        Updates the ObjectListView widget display
        """
        cw = self.col_w
        # change column widths as necessary
        if self.gui_shown:
            cw["name"] = self.procmonOlv.GetColumnWidth(0)
            cw["pid"] = self.procmonOlv.GetColumnWidth(1)
            cw["exe"] = self.procmonOlv.GetColumnWidth(2)
            cw["user"] = self.procmonOlv.GetColumnWidth(3)
            cw["cpu"] = self.procmonOlv.GetColumnWidth(4)
            cw["mem"] = self.procmonOlv.GetColumnWidth(5)
            
        cols = [
            ColumnDefn("name", "left", cw["name"], "name"),
            ColumnDefn("pid", "left", cw["pid"], "pid"),
            ColumnDefn("exe location", "left", cw["exe"], "exe"),
            ColumnDefn("username", "left", cw["user"], "user"),
            ColumnDefn("cpu", "left", cw["cpu"], "cpu"),
            ColumnDefn("mem", "left", cw["mem"], "mem"),
            #ColumnDefn("description", "left", 200, "desc")
            ]
        self.procmonOlv.SetColumns(cols)
        self.procmonOlv.SetObjects(self.procs)
        self.procmonOlv.SortBy(self.sort_col)
        if self.currentSelection:
            self.procmonOlv.Select(self.currentSelection)
            self.procmonOlv.SetFocus()
        self.gui_shown = True
        
    #----------------------------------------------------------------------
    def update(self, event):
        """
        Start a thread to get the pid information
        """
        print "update thread started!"
        self.timer.Stop()
        controller.ProcThread()
        
    #----------------------------------------------------------------------
    def updateDisplay(self, msg):
        """
        Catches the pubsub message from the thread and updates the display
        """
        print "thread done, updating display!"
        self.procs = msg.data
        self.setProcs()
        if not self.timer.IsRunning():
            self.timer.Start(15000)
    
########################################################################
class MainFrame(wx.Frame):
    """"""

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="PyProcMon", size=(1024, 768))
        panel = MainPanel(self)
        
        # set up the statusbar
        self.CreateStatusBar()
        self.StatusBar.SetFieldsCount(3)
        self.StatusBar.SetStatusWidths([200, 200, 200])
        
        # create a pubsub receiver
        Publisher().subscribe(self.updateStatusbar, "update_status")
        
        self.Show()
        
    #----------------------------------------------------------------------
    def updateStatusbar(self, msg):
        """"""
        procs, cpu, mem = msg.data
        self.SetStatusText("Processes: %s" % procs, 0)
        self.SetStatusText("CPU Usage: %s" % cpu, 1)
        self.SetStatusText("Physical Memory: %s" % mem, 2)
        
        
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
    
