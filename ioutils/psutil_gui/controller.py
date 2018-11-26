########################################################################
import psutil
import wx

from model import Process
from threading import Thread
from wx.lib.pubsub import Publisher

########################################################################
class ProcThread(Thread):
    """
    Gets all the process information we need as psutil isn't very fast
    """

    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        Thread.__init__(self)
        self.start() 
        
    #----------------------------------------------------------------------
    def run(self):
        """"""
        pids = psutil.get_pid_list()
        procs = []
        cpu_percent = 0
        mem_percent = 0
        for pid in pids:
            try:
                p = psutil.Process(pid)
                cpu = p.get_cpu_percent()
                mem = p.get_memory_percent()
                new_proc = Process(p.name,
                                   str(p.pid),
                                   p.exe,
                                   p.username,
                                   str(cpu),
                                   str(mem)
                                   )
                procs.append(new_proc)
                cpu_percent += cpu
                mem_percent += mem
            except:
                pass
                
        # send pids to GUI
        wx.CallAfter(Publisher().sendMessage, "update", procs)
        
        number_of_procs = len(procs)
        wx.CallAfter(Publisher().sendMessage, "update_status",
                     (number_of_procs, cpu_percent, mem_percent))
        
            