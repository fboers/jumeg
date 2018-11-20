import wx,sys
import wx, wx.lib.agw.rulerctrl as rc

try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False

try:
    # The Python OpenGL package can be found at
    # http://PyOpenGL.sourceforge.net/
    from OpenGL import GL   as gl
    from OpenGL import GLUT as glut
    haveOpenGL = True
except ImportError:
    haveOpenGL = False

from jumeg.tsvgl.plot2d.jumeg_tsv_plot2d_gl import JuMEG_TSV_PLOT2D_OGL

# from jumeg.tsvgl.plot2d.jumeg_tsv_plot2d_ogl_axis_viewport_ok  import JuMEG_TSV_PLOT2D_OGL

class JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASE(glcanvas.GLCanvas):
    def __init__(self, parent):

        attribList = (glcanvas.WX_GL_RGBA,          # RGBA
                      glcanvas.WX_GL_DOUBLEBUFFER,  # Double Buffered
                      glcanvas.WX_GL_DEPTH_SIZE,24) # 24 bit
                      
        glcanvas.GLCanvas.__init__(self, parent, -1,attribList=attribList,style = wx.DEFAULT_FRAME_STYLE)
       
        self.is_initGL   = False
        self.is_on_draw  = False
        self.is_on_paint = False
        self.is_on_size  = False
             
        self.init = False
        self.context = glcanvas.GLContext(self)
        
      # initial mouse position
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        #self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        #self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        #self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        
        self.Bind(wx.EVT_KEY_DOWN,  self.OnKeyDown)
        self.Bind(wx.EVT_CHAR,  self.OnKeyDown)

    def OnEraseBackground(self,evt):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, evt):
        print " JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASe -> OnSizeEvent"
        #if self.GetContext():
        #if not self.is_initGL:
        #   self.InitGL()
        if self.is_initGL:
           wx.CallAfter(self.DoSetViewport)
           #self.OnReshape(self.size.width,self.size.height)
           self.Refresh(False)
           print " ---> DONE JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASe -> OnSizeEvent"
        #evt.Skip()        
   
    def DoSetViewport(self):
        size = self.size = self.GetClientSize()
        self.SetCurrent(self.context)
        gl.glViewport(0, 0, size.width, size.height)
   
    def OnReshape(self, width, height):
        print " JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASE -> OnReshapeEvent"
        """Reshape the OpenGL viewport based on the dimensions of the window."""
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity() 
        print "   ---> DONE JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASe -> OnReshapeEvent"
        
    def OnPaint(self, event):
        print " JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASe -> OnPaintEvent"   
        if self.is_on_paint:
           return     
        
        self.is_on_paint = True 
         
        if not self.is_initGL:
           self.InitGL()
        
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        
        self.OnDraw( size_mm=dc.GetSizeMM() ) 
        self.SwapBuffers()  
        self.is_on_paint = False       
        print "   ---> DONE JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASe -> OnPaintEvent"
        
    def InitGL(self):
        print" ToDo dummy def initGL overwrite"
        
    def OnDraw(self):
        print" ToDo dummy def OnDraw overwrite"
        
    def OnKeyDown(self, e):

        key = e.GetKeyCode()
      #---escape to quit
        if key == wx.WXK_ESCAPE:
           self.click_on_exit(e)
           
           
    def px2mm(pixels):
        px = float(wx.GetDisplaySize()[1])
        mm = float(wx.GetDisplaySizeMM()[1])
        mmperpx = mm/px
        return mmperpx * pixels



class JuMEG_TSV_PLOT2D_WX_GL_CANVAS(JuMEG_TSV_PLOT2D_WX_GL_CANVAS_BASE):
      def __init__(self, parent=None, *args, **kwargs):
          super(JuMEG_TSV_PLOT2D_WX_GL_CANVAS,self).__init__(parent) #, *args, **kwargs)
          self.gl_plot2d = None
          #self.InitGL()
       
          
      def __get_plot_option(self):
          return self.plot2d.opt
      def __set_plot_option(self,opt):
          self.plot2d.opt = opt
      option = property(__get_plot_option,__set_plot_option)    
     
      def __get_plot_info(self):
          return self.plot2d.info
      def __set_plot_info(self,info):
          self.plot2d.info = info
          self.plot2d.data_channel_selection_is_update = False
         #--- update e.g. channel selction
          self.plot2d.info.update()        
      info = property(__get_plot_info,__set_plot_info)    
            

      def OnKeyDown(self, evt):
          action = None
          
          if not self.is_initGL :
             evt.skip()  #---escape to quit
             
          key = evt.GetKeyCode()      
                  
         #--- scroll time fast by window
          if (wx.GetKeyState(wx.WXK_CONTROL) == True):
             
             if key == (wx.WXK_LEFT):
                #print"FAST REW"               
                action = "FAST_REWIND"      
             elif key == (wx.WXK_RIGHT):
                action = "FAST_FORWARD" 
             elif key == (wx.WXK_HOME):
                action ="START"      
             elif key == (wx.WXK_END):
                action = "END" 
         #----
          elif key == (wx.WXK_F11): 
               action = "TIME_DISPLAY_ALL" 
          elif key ==(wx.WXK_F12): 
               action = "CHANNELS_DISPLAY_ALL" 
                
         #--- scroll time by scroll step 
          elif key == wx.WXK_LEFT:
               #print"LEFT"
               action = "REWIND" 
          elif key == wx.WXK_RIGHT:
               #print "RIGHT"
               action = "FORWARD"
                
       #--- scroll channels  
          elif key == wx.WXK_UP:
               action = "UP"
          elif key == wx.WXK_DOWN:
               action = "DOWN"      
          elif key == wx.WXK_PAGEUP:
               action = "PAGEUP"
          elif key == wx.WXK_PAGEDOWN:
               action = "PAGEDOWN"
          elif key == wx.WXK_HOME:
               action = "TOP"
          elif key == wx.WXK_END:
               action = "BOTTOM"  
         
         #---
          if action:
             #self.plot2d.opt.action(action)
             self.update()  
          
          else:
             evt.Skip()

      def InitGL(self):
          print"JuMEG_TSV_PLOT2D_WX_GL_CANVAS -> InitGL" 
          self.is_initGL = False
          #if self.context:elf.Plot2DCanvas
          dc  = wx.ClientDC(self)
          self.SetCurrent(self.context)
          size = self.size = self.GetClientSize()  
             
          self.gl_plot2d = JuMEG_TSV_PLOT2D_OGL(size=size)
                 
          return self.is_initGL

      def OnDraw(self,size_mm=None):
          print"JuMEG_TSV_PLOT2D_WX_GL_CANVAS -> OnDraw"  
          #if not  self.is_initGL:
          #   print" ---> NOT InitGL"
          #   return
          if self.is_on_draw:
             print" ---> ON DRAW RETURN"
             return
           
          self.is_on_draw  = True
          #dc  = wx.PaintDC(self)
          #self.SetCurrent(self.context)
        
          self.gl_plot2d.size_in_pixel = self.GetClientSize()
          self.gl_plot2d.size_in_mm    = size_mm

          print " ---> "+self.__class__.__name__ +" OnDraw -> plot size"
          print self.gl_plot2d.size_in_pixel 
          print self.gl_plot2d.size_in_mm 
          
        
          #self.gl_plot2d.display()
         
          self.gl_plot2d.test()
         
          self.is_on_draw  = False
      
      def update(self,raw=None,n_channels=None,n_cols=None): #,do_scroll_channels=True,do_scroll_time=True):
           print"JuMEG_TSV_PLOT2D_WX_GL_CANVAS -> update"  
           #if not self.is_initGL :
           #   self.InitGL()
           #else:   
           self.SetCurrent(self.context)
           #if raw :
           #     self.gl_plot2d.init_raw_data(raw=raw,channels2plot=n_channels,cols=n_cols)                
           #elif self.gl_plot2d.data_is_init: 
           #     self.gl_plot2d.update_data() #do_scroll_channels=True,do_scroll_time=True,)
           self.gl_plot2d.test()       
                  #self.plot_axis.range_max = self.plot2d.timepoints[-1]
                  #self.plot_axis.range_min = self.plot2d.timepoints[0]
       
           if self.gl_plot2d.opt.do_scroll:
              print"update-> gl_plot2d.opt.do_scroll"
              self.gl_plot2d.test()     
              #self.Refresh()
               # self.plot_axis.range_max = self.plot2d.timepoints[-1]
                #self.plot_axis.range_min = self.plot2d.timepoints[0]
                
                #self.plot_axis.Refresh()
                    
         
  
    
class JuMEG_TSV_PLOT2D_PANEL(wx.Panel):

      def __init__(self, parent,verbose=False):
          wx.Panel.__init__(self,parent,-1)
          self.verbose   = verbose
          self.SetBackgroundColour("grey")
         #---
          #self._xaxis_panel = wx.Panel(self)
          #self._xaxis_panel.SetBackgroundColour("green")
          #self.XAxisRuler = rc.RulerCtrl(self._xaxis_panel, orient=wx.HORIZONTAL)
          self.XAxisRuler = rc.RulerCtrl(self, orient=wx.HORIZONTAL)
          self.XAxisRuler.SetRange(0.0,1.0)
          
         #---
          #self.Plot2DCanvas= wx.Panel(self)
          #self._plot2d_panel = wx.Panel(self)
          #self._plot2d_panel.SetBackgroundColour("red")
          #self.Plot2DCanvas  = JuMEG_TSV_PLOT2D_WX_GL_CANVAS( self._plot2d_panel )
          self.Plot2DCanvas  = JuMEG_TSV_PLOT2D_WX_GL_CANVAS( self )
          #self.Plot2DCanvas.XAHruler = self.XAxisRuler
         
          self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)
          self.Bind(wx.EVT_CHAR,    self.OnKeyDown)
          
          self.__ApplyLayout()
          #self.Plot2DCanvas.InitGL()
          
      def OnKeyDown(self,evt):
          print"ON KEY DOWN" 
          #self.Plot2DCanvas.OnKeyDown(evt)
           
      def update(self,raw=None,**kwargs):
          # self.Plot2DCanvas.plot2d.Hruler = self.XAxisRuler
          print"update plot"
          #self.Plot2DCanvas.update(raw=raw,**kwargs)
           
      def __ApplyLayout(self):
          vbox = wx.BoxSizer(wx.VERTICAL)    
          #vbox.Add(self._plot2d_panel, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,10)
          vbox.Add(self.Plot2DCanvas, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,10)
          vbox.Add(self.XAxisRuler, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,10)
          
          #vbox.Add(self._xaxis_panel, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND,1)
          self.SetAutoLayout(True)
          self.SetSizer(vbox)   
          self.Show(True)
     
      def __get_verbose(self):
          return self.__verbose
      def __set_verbose(self,v):
          self.__verbose = v
          #self.Plot2DCanvas.opt.verbose = v
      verbose = property(__get_verbose,__set_verbose)    
           
      
     # def __get_plot_option(self):
     #     return self.Plot2DCanvas.option
     # def __set_plot_option(self,opt):
     #     self.Plot2DCanvas.option = opt
     # option = property(__get_plot_option,__set_plot_option)    
     
     # def __get_plot_info(self):
     #     return self.plot_window.info
     # def __set_plot_info(self,info):
     #     self.Plot2DCanvas.info = info
          #self.plot_window.data_channel_selection_is_update = False
         #--- update e.g. channel selction
     #     self.Plot2DCanvas.info.update()        
     # info = property(__get_plot_info,__set_plot_info)    
      """
     #---
      def change_subplot_option(self,raw_is_loaded=False):
          opt = None
          self.Plot2DCanvas.is_on_draw = True           
          # opt = jwx_utils.jumeg_wx_dlg_subplot(opt=self.option)
          self.Plot2DCanvas.is_on_draw=False       
          if opt:
             self.option = opt
             if raw_is_loaded:
                self.Plot2DCanvas.update()

      def change_group_option(self,raw_is_loaded=False):
          info = None
          self.Plot2DCanvas.is_on_draw = True           
          # info = jwx_utils.jumeg_wx_dlg_group(opt=self.info)
          self.Plot2DCanvas.is_on_draw = False       
          if info:
             self.info = info
             if raw_is_loaded:
                self.update()
                
         
           
      """     
          #self.ruler.AddIndicator(id=100, value=0.0)
          #self.ruler.AddIndicator(id=101, value=6.5)
                
          