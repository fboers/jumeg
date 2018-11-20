#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 10 22:35:58 2017

@author: fboers
"""

import freetype

try:
    import wx.lib.wxcairo
    import cairo
    haveCairo = True
except ImportError:
    haveCairo = False


class JuMEG_TSV_OGL_TEXT_CAIRO(object):
      """"
      """
      def __init__(self,font='times.ttf'):
      #def __init__(self,font='/usr/share/fonts/truetype/msttcorefonts/times.ttf'):
          self.__ctx = None
          self.__DC  = None 
         
         #--- int FTGL font rendering
          self.__font_name = font
          self.__font_path = os.getenv('JUMEG_PATH_TSV')+'/fonts/'
          
          # Draw some text
          self.face = wx.lib.wxcairo.FontFaceFromFont(wx.FFont(10, wx.SWISS, wx.FONTFLAG_BOLD))
          
         #ctx.set_font_face(face)
         #ctx.set_font_size(60)
        # ctx.move_to(360, 180)   
        # ctx.show_text("Hello")


          self.clfront   = np.array([0.0,0.0,0.0,1.0],'f')
          self.clback    = np.array([1.0,1.0,1.0,0.0],'f')
          self.font_size = 24
          self.isupdate  = False
          
      def __get_ctx(self):
          return self.__ctx
      ctx =  property(__get_ctx)
      
      def __get_dc(self):
          return self.__dc
      def __set_dc(self,dc):
          self.__ctx =  wx.lib.wxcairo.ContextFromDC(dc)
          self.__dc  = dc
          self.ctx.set_font_face(face)
          self.ctx.set_font_size( self.font_size )
          self.ctx.set_source_rgb(0, 0, 0)
          
          
      DC = property(__get_dc,__set_dc)    
          
      def __get_font(self):
          return self.__font_path+'/'+self.__font_name
      def __set_font(self,f):
          self.__font_name= f          
      font_file = property(__get_font,__set_font)

      def update(self,dc=None):       
      # init font          
         # try:
          print "update"
          if dc:
             self.DC = dc
      
      
      def __get_clfront(self):
          return self.__clfront[0],self.__clfront[1],self.__clfront[2],self.__clfront[3]  
      def __set_clfront(self,v):
          self.__clfront =v  
      clfront = property(__get_clfront,__set_clfront)  
      
      def render(self,xpos,ypos,txt):
          self.ctx.move_to(xpos,ypos)  
          self.ctx.show_text(txt)

           #glUseProgram(self.GLSL.program_id)
          # glEnable(GL_TEXTURE_2D)
          # glEnable(GL_BLEND)
          # glEnable(GL_DEPTH_TEST)
          # glColor3f(1.0,1.0,1.0)
            
          # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
           #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
           #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
           #glBlendFunc(GL_SRC_ALPHA,GL_ZERO)
           #glColor4f(self.clfront[0],self.clfront[1],self.clfront[2],self.clfront[3])
           #glColor4f(self.clfront[0],self.clfront[1],self.clfront[2],1.0)
           #glMatrixMode(GL_MODELVIEW)
               
           #glLoadIdentity()        
           #glPushMatrix()
           #glTranslatef(0,0, 0.0)
           # for idx_chr in str( self.info.index2channel_label(ch_idx) ):
                    
           #self.font.Render("MEG123".encode('utf8'))
                    
          # self.font.Render("MEG123")
                    
           #self.font.Render( str(s) )
          
           #glPopMatrix()
           #glDisable(GL_TEXTURE_2D)
           #glDisable(GL_BLEND)
         










class JuMEG_TSV_OGL_TEXT(object):
      """"
      drawing text like channel labes
      FTGL wrapper CLS
      default font: ./jumeg/tsv/fonts/times.ttf
      linux: choose font from  /usr/share/fonts/truetype/msttcorefonts
      """
      def __init__(self,font='times.ttf'):
      #def __init__(self,font='/usr/share/fonts/truetype/msttcorefonts/times.ttf'):
       
         #--- int FTGL font rendering
          self.__font_name = font
          self.__font_path = os.getenv('JUMEG_PATH_TSV')+'/fonts/'
          self.clfront   = np.array([0.0,0.0,0.0,1.0],'f')
          self.clback    = np.array([1.0,1.0,1.0,0.0],'f')
          self.font_size = (24,72)
          self.isupdate  = False
      
      def __get_font(self):
          return self.__font_path+'/'+self.__font_name
      def __set_font(self,f):
          self.__font_name= f          
      font_file = property(__get_font,__set_font)

      def update(self):       
      # init font          
          try:
              #--- int FTGL font rendering
            #self.fonts = [
            #           FTGL.OutlineFont(self.font_file),
            #           FTGL.PolygonFont(self.font_file),
            #           FTGL.TextureFont(self.font_file),
            #           FTGL.BitmapFont(self.font_file),
            #           FTGL.PixmapFont(self.font_file),
            #          ]
            #  for font in fonts:
            #      self.font.FaceSize(24, 72)
             
            #self.font = FTGL.TextureFont(self.font_file)
            
            # self.font = FTGL.PixmapFont(self.font_file)
            
            
#font="./jumeg/tsv/fonts/times.ttf"
#face = freetype.Face(font) #"Vera.ttf")
#face.set_char_size( 48*64 )
#face.load_char('S')
#bitmap = face.glyph.bitmap
#print bitmap.buffer
#            self.font =
#            self.font.FaceSize(self.font_size[0],self.font_size[1])
#            self.isupdate = True
#          except:
#               print "FTGL can not load font file: " + self.font_file
#               sys.exit(0)         
#         
#          return self.isupdate
      
      
      '''
      def __get_clfront(self):
          return self.__clfront[0],self.__clfront[1],self.__clfront[2],self.__clfront[3]  
      def __set_clfront(self,v):
          self.__clfront =v  
      clfront = property(__get_clfront,__set_clfront)  
      '''
      def render(self,s):
           #glUseProgram(self.GLSL.program_id)
          # glEnable(GL_TEXTURE_2D)
          # glEnable(GL_BLEND)
          # glEnable(GL_DEPTH_TEST)
          # glColor3f(1.0,1.0,1.0)
            
          # glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
           #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
           #glBlendFunc(GL_SRC_ALPHA, GL_ONE)
           #glBlendFunc(GL_SRC_ALPHA,GL_ZERO)
           #glColor4f(self.clfront[0],self.clfront[1],self.clfront[2],self.clfront[3])
           #glColor4f(self.clfront[0],self.clfront[1],self.clfront[2],1.0)
           #glMatrixMode(GL_MODELVIEW)
               
           #glLoadIdentity()        
           #glPushMatrix()
           #glTranslatef(0,0, 0.0)
           # for idx_chr in str( self.info.index2channel_label(ch_idx) ):
                    
           self.font.Render("MEG123".encode('utf8'))
                    
          # self.font.Render("MEG123")
                    
           #self.font.Render( str(s) )
          
           #glPopMatrix()
           glDisable(GL_TEXTURE_2D)
           glDisable(GL_BLEND)
           
      