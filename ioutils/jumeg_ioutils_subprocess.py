#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 23 15:16:46 2018

@author: fboers
-------------------------------------------------------------------------------
ToDo:
implement support for ssh to pc & ssh cluster via PBS protocoll
-------------------------------------------------------------------------------  
https://pythonspot.com/python-subprocess/


for wx log
https://www.blog.pythonlibrary.org/2009/01/01/wxpython-redirecting-stdout-stderr/

"""

import sys,os,shlex,re,wx
from datetime         import datetime as dt
from subprocess       import Popen, PIPE
from threading        import Thread
from wx.lib.pubsub    import pub
from jumeg.jumeg_base import jumeg_base as jb

__version__="2010-11-15-001"


'''
https://gist.github.com/bortzmeyer/1284249
HOST="www.example.org"
# Ports are handled in ~/.ssh/config since we use OpenSSH
COMMAND="uname -a"

ssh = subprocess.Popen(["ssh", "%s" % HOST, COMMAND],
                       shell=False,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
result = ssh.stdout.readlines()
if result == []:
    error = ssh.stderr.readlines()
    print >>sys.stderr, "ERROR: %s" % error
else:
print result

'''
class JuMEG_IoUtils_SubProcThread(Thread):
    """SubProc Worker Thread Class."""

   # ----------------------------------------------------------------------
    def __init__(self,joblist=None,hostinfo={'kernels': 1, 'maxkernels': 1, 'maxnodes': 1, 'name': 'local', 'nodes': 1},verbose=False):
        """Init Worker Thread Class."""
        super().__init__()
        self.joblist = joblist
        self.hostinfo= hostinfo
        self._jobnumber = 0
        self._args    = None
        self._cmd     = None
        self._stdout  = None
        self._stderr  = None
        self.__proc   = None
        self.verbose  = verbose
       # self.start()  # start the thread

    @property
    def job_number(self): return self._jobnumber
   #---
    @property
    def host(self): return self.hostinfo["name"]
   #---
    @property
    def cmd(self): return self._cmd
   #---
    @property
    def args(self): return self._args
   #---
    @property
    def proc(self): return self.__proc
   #---
    def _update_from_kwargs(self,**kwargs):
        self.joblist = kwargs.get("joblist",self.joblist)
        self.hostinfo= kwargs.get("hostinfo",self.hostinfo)

    def post_event(self,message,data):
        wx.CallAfter(lambda *a: pub.sendMessage(message,data=data))

   # ----------------------------------------------------------------------
    def run(self): #,**kwargs):
        """Run Worker Thread."""
        # self._update_from_kwargs(**kwargs)
        if not self.joblist: return

        if self.host == "local":
           self.run_on_local()
        else:
           self.run_on_cluster()

        #wx.CallAfter(self.postTime, i)
        #time.sleep(5)
        #wx.CallAfter(Publisher().sendMessage, "update", "Thread finished!")

   # ----------------------------------------------------------------------
    def run_on_local(self):
        """
         execute command on local host

         Parameter
         ---------
          cmd: string <None>
        """
        self._pidlist = []

        if not self.joblist:
           self.post_event("MAIN_FRAME.MSG.ERROR",data="JuMEG_IoUtils_SubProcess.run_on_local: no command defined")
           return

        self.post_event("MAIN_FRAME.STATUS.BUSY", data=True)

        self.__isBusy = True
        self._args = None

        if not isinstance(self.joblist, list):
           self.joblist = list(self.joblist)

        #if self.verbose:
        #   wx.LogMessage(jb.pp_list2str(self.joblist, head="PBS SubProc Job list: "))
        #   wx.LogMessage(jb.pp_list2str(self.host,    head="PBS SubProc HOST Info:"))

        self._job_number=0
        self.post_event("MAIN_FRAME.STATUS.BUSY", data=True)
        self.__isBusy = True

        for job in self.joblist:
            if isinstance(job, list):
               self._args = job
               self._cmd = " ".join(job)
            else:
               self._args = shlex.split(job)
               self._cmd = job

            if not self._args:
               self.post_event("MAIN_FRAME.MSG.ERROR",data="JuMEG_IoUtils_SubProcess.run_on_local error in <command>")
               return

            if self.verbose:
               self.log_info_process()
               self.log_info_start_process()

           # --- init & start process
            self._args = ['ls','-lisa']
            self.__proc = Popen(self._args, stdout=PIPE, stderr=PIPE)
            self._pidlist.append(self.__proc.pid)

            self._job_number+=1
            wx.LogMessage(" -->RUN SubProc Nr.: {}  PID: {}".format(self.job_number,self.__proc.pid))
            self.post_event("MAIN_FRAME.STB.MSG",data=["RUN", self._args[0], "PID", str(self.__proc.pid)])

            self._stdout, self._stderr = self.__proc.communicate()

            if self.verbose:
               self.log_info_stop_process()
               #self.log_info_stdout()
               #self.log_info_stderr()

        self.post_event("MAIN_FRAME.STATUS.BUSY",data=False)
        self.__isBusy = False

    def run_on_remote(self):  # ,host=None):
        """
        to do implement ssh and host list
        """
        pass

    def run_on_cluster(self):  # ,host=None):
        """
        to do implement ssh and cluster list
        cluster nodes and kernels
        """
        pass

    def log_info_start_process(self):
        wx.LogMessage("  -> start process Host: {} \n".format(self.host))

    def log_info_stop_process(self):
        wx.LogMessage("  -> stop  process Host: {} Time: {}\n".format(self.host))

    def log_info_process(self):
        wx.LogMessage(jb.pp_list2str(self.cmd,head=" -->SubProcess cmd:"))

    def log_info_stdout(self):
        if self._stdout:
           s = str(self._stdout, 'utf-8')
           wx.LogMessage(" -->SubProcess output: " + re.sub(r'\n+', "\n", s).strip())
        else:
           wx.LogMessage(" -->SubProcess no output")

    def log_info_stderr(self):
        if self._stderr:
           s = str(self._stderr, 'utf-8')
           wx.LogError(" -->SubProcess Error: "+ re.sub(r'\n+',"\n" ,s).strip())
        else:
           wx.LogMessage(" -->SubProcess no ERROR")



class JuMEG_IoUtils_SubProcess(object):
    """
    jumeg subclass for subprocess module
    
    local 
    
    ToDo
    -----
    devel version
    implement support for ssh to pc & ssh cluster via PBS protocoll
    """
    def __init__(self):
        super(JuMEG_IoUtils_SubProcess,self).__init__()
        self.verbose  = None
        self._args    = None
        self._cmd     = None
        self._stdout  = None
        self._stderr  = None
        self._host    = "local"

        self._hostinfo_default = {'kernels': 1, 'maxkernels': 1, 'maxnodes': 1, 'name': 'local', 'nodes': 1}
        self.hostinfo = self._hostinfo_default

        self.__proc   = None
        self.__isBusy = False
        self.verbose  = True
        self._init_pubsub_messages()
        self.SubProcTHRD = JuMEG_IoUtils_SubProcThread()
        #self.host_choices=["local","ssh","cluster"]
        
        
        # ToDo get list of PCs & clusters
   #---
    @property
    def cmd(self): return self._cmd
   #---
    @property
    def args(self): return self._args
   #---
    @property
    def proc(self): return self.__proc
   #---   
    @property
    def isBusy(self): return self.__isBusy
   #---
    @property
    def host(self): return self._host
    @host.setter
    def host(self,v): self._host=v


    def _init_pubsub_messages(self):
        pub.subscribe(self.run,       'SUBPROCESS.RUN.START')

        #pub.subscribe(self.run_on_remote, 'SUBPROCESS.RUN.REMOTE')
        #pub.subscribe(self.run_on_cluster,'SUBPROCESS.RUN.CLUSTER')
        pass

    def run(self,joblist=None,hostinfo=None,verbose=False):
        """
        https://wiki.wxpython.org/LongRunningTasks

        :param joblist:
        :param hostinfo:
        :return:
        """
        if self.isBusy: return

        self.__isBusy=True

        if hostinfo:
           self.hostinfo=hostinfo

       #--- make new thrd
       #--- https://www.tutorialspoint.com/python3/python_multithreading.htm
        thrd = JuMEG_IoUtils_SubProcThread(joblist=joblist,hostinfo=self.hostinfo,verbose=verbose)
        thrd.start()
       # thrd.join()  # this will wait till thrd ends

       # if self.host == "local":
       #    thread.start_new_thread( self.run_on_local() )
       # else:
        #   thread.start_new_thread( self.run_on_cluster() )

        self.__isBusy=False
    
        
''' 
import wx, sys
from threading import Thread
import time
import subprocess


class mywxframe(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self,None)
        pnl = wx.Panel(self)
        szr = wx.BoxSizer(wx.VERTICAL)
        pnl.SetSizer(szr)
        szr2 = self.sizer2(pnl)
        szr.Add(szr2, 1, wx.ALL|wx.EXPAND, 10)
        log = wx.TextCtrl(pnl, -1, style= wx.TE_MULTILINE, size = (300, -1))
        szr.Add(log, 0, wx.ALL, 10)
        btn3 = wx.Button(pnl, -1, "Stop")
        btn3.Bind(wx.EVT_BUTTON, self.OnStop)
        szr.Add(btn3, 0, wx.ALL, 10)
        self.CreateStatusBar()

        redir = RedirectText(log)
        sys.stdout=redir

        szr.Fit(self)
        self.Show()

    def sizer2(self, panel):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tc2 = wx.TextCtrl(panel, -1, 'Set Range', size = (100, -1))
        btn2 = wx.Button(panel, -1, "OK",)
        self.Bind(wx.EVT_BUTTON, self.OnStart, btn2)
        sizer.Add(self.tc2, 0, wx.ALL, 10)
        sizer.Add(btn2, 0, wx.ALL, 10)
        return sizer


    def OnStart(self, event):
        self.p=subprocess.Popen(["C:\Python27\python.exe",'P:\Computing and networking\Python\Learning programs\hello_world.py'])

    def OnStop(self, event):
        self.p.terminate()

    def write(self, *args):
        print args

class RedirectText(object):
    def __init__(self, aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self, string):
        (self.out.WriteText, string)


app = wx.App()
frm = mywxframe()
app.MainLoop()


TextCtrl update by using wx.CallAfter

# spawn the new process, and redirecting stdout and stderr into this process
proc = subprocess.Popen([PathToCurrentPythonInterpreter, pyFilePath],stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
proc.stdin.close()
#create new stdout and stderr stream listener objects
m=StreamWatcher()
n=StreamWatcher()

#create new threads for each listener, when the listener hears something it prints it to the GUI console log area
proc1 = Thread(target=m.stdout_watcher, name='stdout-watcher', args=('STDOUT', proc.stdout))
proc1.daemon=True
proc1.start()
proc2 = Thread(target=n.stderr_watcher, name='stderr-watcher', args=('STDERR', proc.stderr))
proc2.daemon=True
proc2.start()



class StreamWatcher:
    def stdout_watcher(self, identifier, stream):
        #for line in stream:
        for line in iter(stream.readline,b''):
            print line
        if not stream.closed:
            stream.close()
        print "-i- Thread Terminating : ", identifier,"\n"

    def stderr_watcher(self, identifier, stream):
        #for line in stream:
        for line in iter(stream.readline,b''):
            #print (identifier, line)
            print "-e- %s" % line
        if not stream.closed:
            stream.close()
        print "-i- Thread Terminating : ", identifier, "\n"









HOST="127.0.0.1"
ssh = subprocess.Popen(["ssh",
                        "%s" % HOST],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=0)
 
# send ssh commands to stdin
ssh.stdin.write("ls .\n")
ssh.stdin.write("uname -a\n")
ssh.stdin.write("uptime\n")
ssh.stdin.close()

# fetch output
for line in ssh.stdout:
    print(line),
'''


"""
# os.chdir()
cmd='jumeg_merge_meeg.py --eeg_stage=/home/fboers/MEGBoers/data/exp/MEG94T/eeg/MEG94T --meg_stage=/home/fboers/MEGBoers/data/exp/MEG94T/mne --eeg_filename=109887_MEG94T0T_01.vhdr --meg_filename=109887/MEG94T0T/130626_1329/1/109887_MEG94T0T_130626_1329_1_c,rfDC-raw.fif --eeg_response_shift=1000 --meg_stim_channel="STI 014" --bads_list="MEG 007,MEG 142,MEG 156,RFM 011" --eeg_stim_type=STIMULUS --startcode=128 --eeg_stim_channel="STI 014" -r -v'
args = shlex.split(cmd)
print(args)
p = subprocess.Popen(args)

print p
print "DONE"

from subprocess import Popen, PIPE

process = Popen(['swfdump', '/tmp/filename.swf', '-d'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()


from subprocess import Popen, PIPE
 
process = Popen(['cat', 'test.py'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()
print stdout

subprocess.call(args, *, stdin=None, stdout=None, stderr=None, shell=False)
# Run the command described by args. 
# Wait for command to complete, then return the returncode attribute.


 subprocess.check_output(args, *, stdin=None, stderr=None, shell=False, universal_newlines=False)
 # Run command with arguments and return its output as a byte string.
 
 s = subprocess.check_output(["echo", "Hello World!"])
print("s = " + s)
"""