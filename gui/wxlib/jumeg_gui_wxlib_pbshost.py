#!/usr/bin/envn python3
# -+-coding: utf-8 -+-
#----------------------------------------
# Created by fboers at 21.09.18
#----------------------------------------
# Update
#----------------------------------------

import os,json
import wx
from wx.lib.pubsub  import pub
from jumeg.gui.wxlib.utils.jumeg_gui_wxlib_utils_controls import JuMEG_wxControls,JuMEG_wxControlGrid,JuMEG_wxControlButtonPanel

#from jumeg.jumeg_base import JuMEG_Base_Basic
#jb = JuMEG_Base_Basic()


class JuMEG_PBSHosts(object):
    def __init__(self,**kwargs):
        super(JuMEG_PBSHosts, self).__init__()
        self._template_default = {
                           "local":    {"name":"local"    ,"nodes": 1,"maxnodes": 1, "kernels":1,"maxkernels": 1, },
                           "mrcluster":{"name":"mrcluster","nodes": 1,"maxnodes": 10,"kernels":8,"maxkernels": 1, },
                          }  # ,"type":"","alias":""}}
        self._host = "local"
        self._template_path = os.getenv("JUMEG_PATH_TEMPLATE",os.getcwd())
        self._template_name = "jumeg_host_template.json"
        self.update(**kwargs)

    def hostlist(self): return list(self._template.keys())

    def GetHostInfo(self,key=None):
        if key:  return self._template[key]
        return  self._template[self.hostname]

    def _set_param(self, key, v):
        self._template[self._host][key] = v
    def _get_param(self,key):
       return self._template[self._host][key]

    @property
    def template_name(self):
        return self._template_name

    @template_name.setter
    def template_name(self, v):
        self._template_name = v

    @property
    def template_path(self):
        return self._template_path

    @template_path.setter
    def template_path(self, v):
        self._template_path = v
    @property
    def template_file(self): return self.template_path +"/"+self.template_name

    @property
    def hostname(self):    return self._host

    @hostname.setter
    def hostname(self, v): self._host = v

    @property
    def nodes(self):    return self._get_param("nodes")

    @nodes.setter
    def nodes(self, v): self._set_param("nodes", v)

    @property
    def maxnodes(self):    return self._get_param("maxnodes")

    @maxnodes.setter
    def maxnodes(self, v): self._set_param("maxnodes", v)

    @property
    def kernels(self):    return self._get_param("kernels")

    @kernels.setter
    def kernels(self, v): self._set_param("kernels", v)

    @property
    def maxkernels(self):    return self._get_param("maxkernels")

    @maxkernels.setter
    def maxkernels(self, v): self._set_param("maxkernels", v)

    def _update_from_kwargs(self,**kwargs):
         self._template_path = kwargs.get("template_path",self._template_path)
         self._template_name = kwargs.get("template_name",self._template_name)

    def update(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        self.load_host_template()

    def load_host_template(self):
        """ load host template from <JuMEG TEMPLATE PATH> """

        self._template = self._template_default.copy()

        if ( os.path.isfile( self.template_file ) ):
            with open(self.template_file, 'r') as FID:
                 try:
                     self._template = json.load(FID)
                 except:
                     self._template = self._template_default.copy()
                     print("\n\n!!! ERROR NO JSON File Format:\n  ---> " + self._template_file,file=sys.stderr)
                     print("\n\n",file=sys.stderr)

        #jb.pp(self._template,head="HOST Template")

        return self._template


class JuMEG_wxPBSHosts_NodesKernels(wx.PopupTransientWindow):
    """shows spin buttons for nodes and kernels"""
    def __init__(self, parent, style=wx.SIMPLE_BORDER,host=None):
        super().__init__(parent, style)
        self.HOST = host
        self._wx_init()
        self._ApplyLayout()

    def _wx_init(self, **kwargs):
        ctrls = []
        ctrls.append(("SP", "Nodes", [1, self.HOST.maxnodes, 1], self.HOST.nodes, "select number of nodes",None))
        ctrls.append(("SP", "Kernels", [1, self.HOST.maxkernels, 1], self.HOST.kernels,
                      "select number of kernels/cpus",None))

        self.pnl = JuMEG_wxControls(self,label="--- H O S T :  " + self.HOST.hostname.capitalize() +" ---", drawline=True,control_list=ctrls)

    def OnDismiss(self):
        """ copy values to parent HOST obj and destroy window"""
        self.HOST.nodes   = self.pnl.FindWindowByName("SP_NODES").GetValue()
        self.HOST.kernels = self.pnl.FindWindowByName("SP_KERNELS").GetValue()
        #print("HOST Nodes: {}  Kernels: {}".format(self.HOST.nodes,self.HOST.kernels))
        #print("HOST Nodes Max: {}  Kernels Max: {}".format(self.HOST.maxnodes,self.HOST.maxkernels))
        self.Destroy()

    def _ApplyLayout(self):
        """" default Layout Framework """
        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Sizer.Add(self.pnl,1, wx.ALIGN_LEFT | wx.EXPAND| wx.ALL,2)
        self.SetSizer(self.Sizer)
        self.Fit()
        self.Layout()

class JuMEG_wxPBSHosts(wx.Panel):
    '''
    HOST Panel
    select Host from list of host e.g. local,cluster,
    select nodes and kernels
    '''
    def __init__(self, parent, **kwargs):
        super().__init__(parent=parent, id=wx.ID_ANY, style=wx.SUNKEN_BORDER)
        self.HOST = JuMEG_PBSHosts(**kwargs)
        self._init(**kwargs)

    def SetVerbose(self,value=False):
        self.verbose = value

    def _update_from_kwargs(self, **kwargs):
        self.verbose = kwargs.get("verbose", False)
        self.debug   = kwargs.get("debug", False)
        self.prefix  = kwargs.get("prefix", "PBS_HOSTS")
        self.bg      = kwargs.get("bg",    wx.Colour([230, 230, 230]))
        self.bg_pnl  = kwargs.get("bg_pnl",wx.Colour([240, 240, 240]))

    def _init_pubsub(self):
        """"
        init pubsub call
        """
        pub.subscribe(self.SetVerbose, 'MAIN_FRAME.VERBOSE')

    def _wx_init(self, **kwargs):
        """ init WX controls """
        self.SetBackgroundColour(self.bg)
       # --- PBS Hosts
        ctrls = []
        ctrls.append(("BT", "BT_HOST", "Hosts", "update host list",None))
       # ctrls.append(("BT", "BT_INFO", "Info", "info",None))
        ctrls.append(("COMBO", "COMBO_HOST", "COMBO_HOST", self.HOST.hostlist(), "select a host",None))
        ctrls.append(("FLBT", "FLBT_NODES_KERNELS", "Nodes / Kernels", "select number of nodes and kernels", None))

        self.pnl = JuMEG_wxControlGrid(self,label=None, drawline=False,control_list=ctrls, cols=len(ctrls) + 4,AddGrowableCol=[1])
        self.pnl.SetBackgroundColour(self.bg_pnl)
        self.FindWindowByName("COMBO_HOST").SetValue(self.HOST.hostname)
        self.Bind(wx.EVT_BUTTON, self.ClickOnCtrl)
        self.Bind(wx.EVT_COMBOBOX,self.ClickOnCtrl)

    def update(self, **kwargs):
        pass

    def _init(self, **kwargs):
        """" init """
        self._update_from_kwargs(**kwargs)
        self._wx_init()
        self._init_pubsub()
        self.update()
        self._ApplyLayout()

    def OnShowNodesKernels(self, evt):
        print(" ==> MAIN HOST name: " +self.HOST.hostname)
        wxNK = JuMEG_wxPBSHosts_NodesKernels(self,style=wx.SIMPLE_BORDER,host=self.HOST)
        btn = evt.GetEventObject()
        pos = btn.ClientToScreen( (0,0) )
        sz =  btn.GetSize()
        wxNK.Position(pos, (0, sz[1]))
        wxNK.Popup()

    def info(self):
        print(" ==> PBS HOST Info: " +self.HOST.hostname)
        print("HOST Nodes: {}  Kernels: {}".format(self.HOST.nodes,self.HOST.kernels))
        print("HOST Nodes Max: {}  Kernels Max: {}".format(self.HOST.maxnodes,self.HOST.maxkernels))
        print("====")

    def ClickOnCtrl(self, evt):
        obj = evt.GetEventObject()
        if obj.GetName().upper().startswith("COMBO_HOST"):
           self.HOST.hostname = obj.GetValue()
        elif obj.GetName().upper().startswith("FLBT_NODES_KERNELS"):
             self.OnShowNodesKernels(evt)
        #elif not obj.GetName().upper().startswith("WXSPINCTRL"):
            #self.info()

    def _ApplyLayout(self):
        """" default Layout Framework """
        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.Sizer.Add(self.pnl,1, wx.ALIGN_LEFT | wx.EXPAND| wx.ALL,2)
        self.SetSizer(self.Sizer)
        self.Fit()
        self.SetAutoLayout(1)
        self.GetParent().Layout()



