#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""
implementation of FreeType Class for fast text rendering within opengl context
copied from
https://github.com/rougier/freetype-py
FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier

Created on Mon Oct 16 13:18:57 2017

@author: fboers


"""

import numpy
from freetype  import *
#import freetype  as FT
import OpenGL.GL as gl
import OpenGL.GLUT as glut

#face = freetype.Face("Vera.ttf")
#face.set_char_size( 48*64 )
#face.load_char('S')
#bitmap = face.glyph.bitmap
#print bitmap.buffer



class JuMEG_TSV_OGL_FreeTypeFont(object):
    """
    implementation of FreeType Class for fast text rendering within opengl context
    copied from
    https://github.com/rougier/freetype-py
    FreeType high-level python API - Copyright 2011-2015 Nicolas P. Rougier

    Created on Mon Oct 16 13:18:57 2017

    @author: fboers
    """
 
    def __init__(self,font='/home/fboers/MEGBoers/megtools/python/freetype-py-master/examples/VeraMono.ttf',size=24 ):
        
      #--- font
        self.face = None
        self._font = font
        self._size = size
        self._fontfilename=font
      #--- texture 
        self.texid  = None    
        self.base   = None
        self.text   = "MEG 123"
    #def __get_face(self):
    #    return self._face 
    #def __set_face(self):
    #   self._face = freetype.Face(self._font) 
    
    def __get_fontfilename(self):
        return self._fontfilename
    def __set_fontfilename(self,v):
        self._fontfilename=v
    fontfilename=property(__get_fontfilename,__set_fontfilename)
    
    def update(self):
        self.makefont()
        
    def makefont(self): #,filename,size):
    
     #--- Load font  and check it is monotype
       self.face = Face( self.fontfilename )
       self.face.set_char_size(self._size*64 )
       if not self.face.is_fixed_width:
          raise 'Font is not monotype'

    # Determine largest glyph size
       width, height, ascender, descender = 0, 0, 0, 0
       for c in range(32,128):
           self.face.load_char( chr(c), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
           bitmap    = self.face.glyph.bitmap
           width     = max( width, bitmap.width )
           ascender  = max( ascender, self.face.glyph.bitmap_top )
           descender = max( descender, bitmap.rows-self.face.glyph.bitmap_top )
       height = ascender+descender

    # Generate texture data
       Z = numpy.zeros((height*6, width*16), dtype=numpy.ubyte)
       for j in range(6):
           for i in range(16):
               self.face.load_char(chr(32+j*16+i), FT_LOAD_RENDER | FT_LOAD_FORCE_AUTOHINT )
               bitmap = self.face.glyph.bitmap
               x = i*width  + self.face.glyph.bitmap_left
               y = j*height + ascender - self.face.glyph.bitmap_top
               Z[y:y+bitmap.rows,x:x+bitmap.width].flat = bitmap.buffer

    # Bound texture
       self.texid = gl.glGenTextures(1)
       gl.glBindTexture( gl.GL_TEXTURE_2D, self.texid )
       gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR )
       gl.glTexParameterf( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR )
       gl.glTexImage2D( gl.GL_TEXTURE_2D, 0, gl.GL_ALPHA, Z.shape[1], Z.shape[0], 0,
                        gl.GL_ALPHA, gl.GL_UNSIGNED_BYTE, Z )

    # Generate display lists
       dx, dy = width/float(Z.shape[1]), height/float(Z.shape[0])
       self.base = gl.glGenLists(8*16)
       for i in range(8*16):
           c = chr(i)
           x = i%16
           y = i//16-2
           gl.glNewList(self.base+i, gl.GL_COMPILE)
           if (c == '\n'):
               gl.glPopMatrix( )
               gl.glTranslatef( 0, -height, 0 )
               gl.glPushMatrix( )
           elif (c == '\t'):
               gl.glTranslatef( 4*width, 0, 0 )
           elif (i >= 32):
               gl.glBegin( gl.GL_QUADS )
               gl.glTexCoord2f( (x  )*dx, (y+1)*dy ), gl.glVertex( 0,     -height )
               gl.glTexCoord2f( (x  )*dx, (y  )*dy ), gl.glVertex( 0,     0 )
               gl.glTexCoord2f( (x+1)*dx, (y  )*dy ), gl.glVertex( width, 0 )
               gl.glTexCoord2f( (x+1)*dx, (y+1)*dy ), gl.glVertex( width, -height )
               gl.glEnd( )
               gl.glTranslatef( width, 0, 0 )
           gl.glEndList( )



    def glprint(self,text,xpos=0.0,ypos=0.0,zpos=0.0,color=[0.4,0.5,1.0,1.0] ):
        if color:
           gl.glColor4f(color[0],color[1],color[2],color[3])  
       # gl.glRasterPos2f( xpos,ypos )   
        self.glprint_ord( [ord(c) for c in text]) #,xpos=xpos,ypos=ypos )
        print "TEXT -> "+ text
           
    def glprint_ord(self,ord_list) : #,xpos=None,ypos=None):
        """ may faster with lookup table???"""
        gl.glListBase( FT.base )
        gl.glCallLists( ord_list )                    
   
    
def on_display():
      
    gl.glClearColor(1,1,1,1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glBindTexture( gl.GL_TEXTURE_2D, FT.texid )
    gl.glColor(0,0,0,1)
    gl.glPushMatrix( )
    gl.glTranslate( 1, 0, 0 )
    gl.glPushMatrix( )
    gl.glLoadIdentity( ) 
    idx=1.0
    while idx < 5:
        gl.glColor(0,1.0/ idx,0,1)
        
        text="MEG %03f"%(idx)
        print text
        #gl.glTranslate( 10,idx*12, 0 ) 
        gl.glRasterPos3f( 10.0,idx * 12.0,0.0 ) 
        FT.glprint( text,xpos=0,ypos=12*idx )    
        #gl.glCallLists( [ord(c) for c in FT.text] )
        #gl.glCallLists( [ord(c) for c in FT.text] )
        idx+=1
        
    gl.glPopMatrix( )
    gl.glPopMatrix( )
    glut.glutSwapBuffers( )

def on_reshape( width, height ):
    gl.glViewport( 0, 0, width, height )
    gl.glMatrixMode( gl.GL_PROJECTION )
    gl.glLoadIdentity( )
    gl.glOrtho( 0, width, 0, height, -1, 1 )
   # gl.glMatrixMode( gl.GL_MODELVIEW )
    #gl.glLoadIdentity( )

def on_keyboard( key, x, y ):
    if key == '\033': sys.exit( )


if __name__ == '__main__':
    import sys
    FT=JuMEG_TSV_OGL_FreeTypeFont()
    
    glut.glutInit( sys.argv )
    glut.glutInitDisplayMode( glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH )
    glut.glutCreateWindow( "Freetype OpenGL" )
    glut.glutReshapeWindow( 600, 1000 )
    glut.glutDisplayFunc( on_display )
    glut.glutReshapeFunc( on_reshape )
    glut.glutKeyboardFunc( on_keyboard )
    gl.glTexEnvf( gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_MODULATE )
    gl.glEnable( gl.GL_DEPTH_TEST ) 
    gl.glEnable( gl.GL_BLEND )
    gl.glEnable( gl.GL_COLOR_MATERIAL )
    gl.glColorMaterial( gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE )
    gl.glBlendFunc( gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA )
    gl.glEnable( gl.GL_TEXTURE_2D )
    FT.makefont()
    glut.glutMainLoop( ) 