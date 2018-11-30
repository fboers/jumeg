#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 28.11.18
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

class JuMEG_PBSHostsInfoSL(object):
   """ """
   __slots__ =["name","nodes","maxnodes","kernels","maxkernels","python_version"]

   def __init__(self,**kwargs):
       super().__init__()
       self._init(**kwargs)


   @property
   def hostname(self):    return str(self._get_param("name"))
   @hostname.setter
   def hostname(self, v): self._set_param("name",v)

   def info(self,key=None):
        if key:  return self._param[key]
        return  self._param

   def _update_from_kwargs(self,**kwargs):
       for k in self.__slots__:
           print(k)
           print( kwargs.get(k,self._param[k]) )

   def _init(self,**kwargs):
       self._update_from_kwargs(**kwargs)


JSL=JuMEG_PBSHostsInfoSL(name="TESTWAS")