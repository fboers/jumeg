#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 09:24:01 2020
@author: lkurth
"""
import os
from pubsub import pub

___version__ = "2020-06-14-001"

class FileList():
   
   def __init__(self):
      self._file_list = list()
      self._name      = "FILE_LIST"
      self._filename  = None
      self._init_pubsub()
   
   @property
   def name(self): return self._name

   @property
   def filename(self): return self._filename
   @property
   def dirname(self):
       if self._filename:
          return os.path.dirname(self._filename)
       return None
   @property
   def basename(self):
       if self._filename:
          return os.path.basename(self._filename)
       return None

   @property
   def files(self): return self._file_list
   
   @property
   def counts(self): return len(self._file_list)
   @property
   def n_files(self): return len(self._file_list)
   
   def _init_pubsub(self):
       pass

   def expandvars(self,v):
      """
      expand env's from string works on list or string
       => expandvars and expanduser
      :param v: list of strings  or string
      :return: input with expanded env's
      """
      if not v: return None
      if isinstance(v,(list)):
         for i in range(len(v)):
            v[i] = os.path.expandvars(os.path.expanduser(str(v[i])))
         return v
   
      return os.path.expandvars(os.path.expanduser(str(v)))

   def _read_lines(self, FH):
      self._file_list=list()
      for line in FH:
         line = FH.readline().strip()
         if line.startswith("#"): continue
         self._file_list.append(line)
        
      return self._file_list
         
   def open(self,fname,sort=True):
      """
      
      Parameters
      ----------
      fname
      sort

      Returns
      -------
      file list
      """
    
      self.clear()
      
      if fname:
         fname= self.expandvars(fname)
         if os.path.exists(fname):
            with open(fname,"r") as FH:
                 self._read_lines(FH)
            self._filename = fname
            if sort:
               self._file_list.sort()
      else:
         pub.sendMessage("MSG.WARNING",data="Can not load file names from file list !!!\n  -> no such file: {}".format(fname))

      pub.sendMessage(self._name,data=self._file_list)
      return self._file_list

   def get_auto_fname(self,flist=None):
       """
       auto generated full file name for tmp list file
       Parameters
       ----------
       flist: <None>

       Returns
       -------
       full filename
       """
       if not flist: return None
       f,ext = self.basename.split(".",-1)
       if isinstance(flist,(list)):
          postfix= os.path.basename(flist[0]).split("_")[0]
          postfix+="-"+ os.path.basename(flist[-1]).split("_")[0]
       else:
          postfix= os.path.basename(flist).split("_")[0]
       postfix += "_{}_".format(len(flist)) + os.getenv("USER")+"."+ext
       
       fout = os.path.join(self.dirname,f+"_"+postfix)
       return fout
   
   def save(self,fname,flist=None,overwrite=True):
      """

      Parameters
      ----------
      fname
      sort

      Returns
      -------
      file list
      """
      if not flist: return
      if not isinstance(flist,(list)):
         flist=[flist]
      
      fname = self.expandvars(fname)
      
      if not overwrite:
         if os.path.isfile(fname): return None
         
      if fname:
         if os.path.exists(os.path.dirname(fname)):
            with open(fname,"w") as FH:
                 FH.write('\n'.join(flist))
         return fname
      
   def get_basenames(self,index=None):
       
       if isinstance(index,list):
         return [ os.path.basename( self._file_list[i] ) for i in index]
       elif isinstance(index,int):
         return os.path.basename( self._file_list[index] )
       else:
         return [ os.path.basename( self._file_list[i] ) for i in range( self.counts ) ]
       
   
   def get_files(self, index):
      if isinstance(index,list):
         return [self._file_list[i] for i in index]
      elif isinstance(index,int):
         return self._file_list[index]
      else:
         return self._files
      
   
   def remove_file(self,index):
      self._file_list.pop(index)

   def clear(self):
       self._file_list = []
       self._filename  = None
       

if __name__=="__main__":        
   reader = FileList()
   f=reader.read_file("intext_meeg_filelist.txt")    
   print(f)