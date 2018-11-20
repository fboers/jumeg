#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# draw freetype text for JuMEG Timeseries Viewer
# copied and modified by F Boes
# update 07.11.2017
#-----------------------------------------------------------------------------
# original source
# https://github.com/rougier/freetype-py
#  FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier
#  Distributed under the terms of the new BSD license.
#  modified example source code:
# Subpixel rendering AND positioning using OpenGL and shaders.
# -----------------------------------------------------------------------------

import os
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLUT as glut
from jumeg.tsv.freetype.texture_font import TextureFont, TextureAtlas
from jumeg.tsv.freetype.shader import Shader


vert='''

uniform sampler2D texture;
uniform vec2 pixel;
uniform vec4 text_color; //FB
attribute float modulo;
varying float m;
void main() {
    gl_FrontColor = gl_Color;
    gl_TexCoord[0].xy = gl_MultiTexCoord0.xy;
    //gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    gl_Position =  gl_Vertex;
       
    m = modulo;
}
'''

frag='''
uniform sampler2D texture;
uniform vec2 pixel;
uniform vec4 text_color;  //FB
varying float m;

void main() {
    float gamma = 1.0;

    vec2 uv      = gl_TexCoord[0].xy;
    vec4 current = texture2D(texture, uv);
    vec4 previous= texture2D(texture, uv+vec2(-1,0)*pixel);

    current  = pow(current,  vec4(1.0/gamma));
    previous = pow(previous, vec4(1.0/gamma));

    float r = current.r;
    float g = current.g;
    float b = current.b;
    float a = current.a;
    if( m <= 0.333 )
    {
        float z = m/0.333;
        r = mix(current.r, previous.b, z);
        g = mix(current.g, current.r,  z);
        b = mix(current.b, current.g,  z);
    }
    else if( m <= 0.666 )
    {
        float z = (m-0.33)/0.333;
        r = mix(previous.b, previous.g, z);
        g = mix(current.r,  previous.b, z);
        b = mix(current.g,  current.r,  z);
    }
   else if( m < 1.0 )
    {
        float z = (m-0.66)/0.334;
        r = mix(previous.g, previous.r, z);
        g = mix(previous.b, previous.g, z);
        b = mix(current.r,  previous.b, z);
    }

   float t = max(max(r,g),b);
 
//--FB
   vec4 color = vec4(text_color.rgb, (r+g+b)/2.);
   //gl_FragColor = t*color + (1.-t)*vec4(r,g,b, min(min(r,g),b));
   //gl_FragColor = vec4( color.rgb, color.a);
   //gl_FragColor = color;
   
   //float t = max(max(r,g),b);
   //vec4 color = vec4(0.,1.,0., (r+g+b)/2.);
   color = t*color + (1.-t)*vec4(r,g,b, min(min(r,g),b));
   gl_FragColor = vec4( color.rgb, color.a);

}
'''

class Label:
    def __init__(self, text, font, color=(0.0, 0.0, 0.0, 1.0),  x=0, y=0,                  
                 width=None, height=None, anchor_x='left', anchor_y='baseline'):
        self.text     = text
        #self.shader   = None
        self.vertices = np.zeros((len(text)*4,3), dtype=np.float32)
        self.indices  = np.zeros((len(text)*6, ), dtype=np.uint)
        self.colors   = np.zeros((len(text)*4,4), dtype=np.float32)
        self.texcoords= np.zeros((len(text)*4,2), dtype=np.float32)
        self.attrib   = np.zeros((len(text)*4,1), dtype=np.float32)
        
        pen = [x,y]
        prev = None

        for i,charcode in enumerate(text):
            glyph = font[charcode]
            kerning = glyph.get_kerning(prev)
            x0 = pen[0] + glyph.offset[0] + kerning
            dx = x0-int(x0)
            x0 = int(x0)
            y0 = pen[1] + glyph.offset[1]
            x1 = x0 + glyph.size[0]
            y1 = y0 - glyph.size[1]
            u0 = glyph.texcoords[0]
            v0 = glyph.texcoords[1]
            u1 = glyph.texcoords[2]
            v1 = glyph.texcoords[3]

            index     = i*4
            indices   = [index, index+1, index+2, index, index+2, index+3]
            vertices  = [[x0,y0,1],[x0,y1,1],[x1,y1,1], [x1,y0,1]]
            texcoords = [[u0,v0],[u0,v1],[u1,v1], [u1,v0]]
            colors    = [color,]*4

            self.vertices[i*4:i*4+4]  = vertices
            self.indices[i*6:i*6+6]   = indices
            self.texcoords[i*4:i*4+4] = texcoords
            self.colors[i*4:i*4+4]    = colors
            self.attrib[i*4:i*4+4]    = dx
            pen[0] = pen[0] + glyph.advance[0]/64.0 + kerning
            pen[1] = pen[1] + glyph.advance[1]/64.0
            prev = charcode

        width = pen[0]-glyph.advance[0]/64.0+glyph.size[0]

        if anchor_y == 'top':
            dy = -round(font.ascender)
        elif anchor_y == 'center':
            dy = +round(-font.height/2-font.descender)
        elif anchor_y == 'bottom':
            dy = -round(font.descender)
        else:
            dy = 0

        if anchor_x == 'right':
            dx = -width/1.0
        elif anchor_x == 'center':
            dx = -width/2.0
        else:
            dx = 0
        self.vertices += (round(dx), round(dy), 0)


class JuMEG_TSV_FreeType_Text(object):
      """"
      """
      def __init__(self,font='Vera.ttf',size=12,path=None):
          self._font_size = size
          self._font_name = font
          self.font       = None
          #if path:
          #   self._font_path = path
          #else:   
          self.font_path = os.getenv('JUMEG_PATH_TSV')+'/fonts/'
          
          self.font_filename = self.font_path+"/"+self._font_name  
        
        ##!!!! TODO ck glInit
          print self.font_filename
          self.atlas = TextureAtlas(512,512,3)
          self.font  = TextureFont(self.atlas,self.font_filename,self._font_size)
          #self.text_color=np.array([1.0,0.0,0.0,1.0],dtype=np.float32)
          self.text_color=(1.0,0.0,0.0,1.0)
          #self.atlas.upload()
          self.init_shader() # =Shader(vert,frag)
          self.label_list   = []
          
          #self.vbo_id = None
          #glBindBuffer(GL_ARRAY_BUFFER, self.vbo_id)
          #glBufferData(GL_ARRAY_BUFFER, 4*len(self.data),self.data,self.gl_draw_type)
   
          #self.label        = Label()
          #self.label.font   = self.font
          #self.label.shader = self.shader
      def init_shader(self):
          #self.shader.unbind()
          self.shader=Shader(vert,frag)
          
      def append(self,text=None,x=0,y=0): #,color=(1.0,1.0,1.0,0.0) ):
          L = Label(text,font=self.font,x=x, y=y)
          #L.color_text=color
          #L.font   = self.font
          #L.shader = self.shader
          # L.init(text=text)
          self.label_list.append(L)
      
      def reset(self):
          self.label_list = []  
          self.shader.unbind()
          gl.glDeleteProgram(self.shader.handle);
          self.shader=Shader(vert,frag) 
          
      def draw(self)    :
          #gl.glClearColor(0.5,0.5,0.5,1)
          #gl.glClearColor(1,1,1,1)
          #gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
         
          gl.glBindTexture( gl.GL_TEXTURE_2D, self.atlas.texid )
     
          gl.glEnable( gl.GL_TEXTURE_2D )
          gl.glDisable( gl.GL_DEPTH_TEST )

          gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
          gl.glEnableClientState(gl.GL_COLOR_ARRAY)
          gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
          gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
          
          gl.glColor4f( 0.0, 0.0, 0.0, 1.0 )
          
          gl.glEnable( gl.GL_BLEND )
          gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
          gl.glBlendColor( 0.0, 0.0, 0.0, 1.0 )
          
          #self.shader=Shader(vert,frag)
          self.shader.bind()
          self.shader.uniformi('texture', 0)
          self.shader.uniformf('pixel', 1.0/512, 1.0/512)
          self.shader.uniformf('text_color', 0.5,1.0,0.0,1.0 )#*self.text_color )
          #glUniform4fv('input_color',1, self.text_color)
          
          for label in self.label_list:
             # gl.glColor( *label.color_text )
             # gl.glBlendColor( *label.color_blend )
              #print label.colors
              gl.glVertexPointer(3, gl.GL_FLOAT, 0, label.vertices)
              gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, label.texcoords)
             
              gl.glEnableVertexAttribArray( 1 );
              gl.glVertexAttribPointer( 1, 1, gl.GL_FLOAT, gl.GL_FALSE, 0, label.attrib)
          
              gl.glDrawElements(gl.GL_TRIANGLES, len(label.indices),
                                 gl.GL_UNSIGNED_INT, label.indices)
            
              gl.glDisableVertexAttribArray( 1 );
          
          self.shader.unbind()
          gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
          gl.glDisableClientState(gl.GL_COLOR_ARRAY)
          gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
          gl.glDisable( gl.GL_TEXTURE_2D )
          gl.glDisable( gl.GL_BLEND ) 
    
    
    

if __name__ == '__main__':
    import sys

    #atlas = TextureAtlas(512,512,3)

    def on_display( ):
        gl.glClearColor(0.5,0.5,0.5,1)
        #gl.glClearColor(1,1,1,1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
       # gl.glBindTexture( gl.GL_TEXTURE_2D, JFT.atlas.texid )
        #for label in labels:
        #    label.draw()
        JFT.draw()
        #gl.glColor(0,0,0,1)
        #gl.glBegin(gl.GL_LINES)
        #gl.glVertex2i(15,0)
        #gl.glVertex2i(15, 330)
        #gl.glVertex2i(225, 0)
        #gl.glVertex2i(225, 330)
        #gl.glEnd()
        glut.glutSwapBuffers( )

    def on_reshape( width, height ):
        gl.glViewport( 0, 0, width, height )
        gl.glMatrixMode( gl.GL_PROJECTION )
        gl.glLoadIdentity( )
        gl.glOrtho( 0, width, 0, height, -1, 1 )
        gl.glMatrixMode( gl.GL_MODELVIEW )
        gl.glLoadIdentity( )

    def on_keyboard( key, x, y ):
        if key == '\033':
            sys.exit( )

    glut.glutInit( sys.argv )
    glut.glutInitDisplayMode( glut.GLUT_DOUBLE | glut.GLUT_RGBA | glut.GLUT_DEPTH )
    glut.glutCreateWindow( "Freetype OpenGL" )
    glut.glutReshapeWindow( 240, 900 )
    glut.glutDisplayFunc( on_display )
    glut.glutReshapeFunc( on_reshape )
    glut.glutKeyboardFunc( on_keyboard )
    JFT = JuMEG_TSV_FreeType_Text()
    #JFT.atlas.upload()
    
    #font_name     = 'Vera.ttf'
    #font_path     = os.getenv('JUMEG_PATH_TSV')+'/fonts/'
    #font_filename = font_path +"/" + font_name  
    #font = TextureFont(atlas, font_filename, 9)
    #text = "|... A Quick Brown Fox Jumps Over The Lazy Dog"
    #labels = []
    x,y = 20,900
    for i in range(10):
        JFT.append(text="MEG %03d"%(i+1), x=x, y=y )  #,color=(1.0,1.0,1.0/(i+0.001),1.0) )
        
        x += 0.1000000000001
        y -= 40
    JFT.atlas.upload()
    JFT.shader = Shader(vert,frag)
    glut.glutMainLoop( )


      
          
'''          

   gl.glOrtho( 0, w, 0, h, -1, 1 )
         # gl.glMatrixMode( gl.GL_MODELVIEW )
         # gl.glLoadIdentity( )

          # self.text.atlas.upload()
         
          gl.glViewport(0,0,self.size_in_pixel.width,self.size_in_pixel.height)
          
          idx = 0 
          self.text.reset()
          for selected_ch_idx in range( self.opt.channels.idx_start,self.opt.channels.idx_end_range): #self.n_channels ):
              ch_idx = self.selected_channel_index[selected_ch_idx]
              label  = self.info.index2channel_label(ch_idx)
              #gl.glViewport(vpm[idx,0],vpm[idx,1],vpm[idx,2],vpm[idx,3])
              
              x = vpm[idx,0]+vpm[idx,2]/2.0 #-0.9 #+ 1.0/self.size_in_pixel.width  * idx
              y = vpm[idx,1]# - 2.0/(idx +1)
              self.text.append(text=label, x=x,y=y)   #vpm[idx,0]+vpm[idx,2]/2.0,y=vpm[idx,1] )
              #self.draw_channel_label_raster(ch_idx,x=x,y=y)
              #glColor4f(1.0,0.0,1.0,1.0)  
              print label
              print x
              print y
              
              idx +=1
          self.text.atlas.upload()
          self.text.draw()
          gl.glUseProgram(0)  
          gl.glFlush()
'''