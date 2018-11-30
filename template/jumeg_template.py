"""
JuMEG Template Class
---------------------------------------------------------------------
 set env variables to the path of your templates files
 JUMEG_PATH_TEMPLATE
 JUMEG_PATH_TEMPLATE_EXPERIMENTS
 JUMEG_PATH_TEMPLATE_EPOCHER
----------------------------------------------------------------------
 r/w jumeg experiment template files in json format
 r/w jumeg epocher    template files in json format
----------------------------------------------------------------------
 file name:
 <experiment>_jumeg_experiment_template.json
 <experiment>_jumeg_epocher_template.json
----------------------------------------------------------------------
 default_jumeg_experiment_template.json
 default_jumeg_epocher_template.json
----------------------------------------------------------------------
from jumeg.template.jumeg_template import JuMEG_Template_Experiments

"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de>
#
#--------------------------------------------
# Date: 21.11.18
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
# 21.11.18
#--------------------------------------------

import glob, os, re, sys
import json
from jumeg.jumeg_base import JuMEG_Base_Basic

__version__='2018-11-21.001'

class dict2obj(dict):
    def __init__(self, dict_):
        super(dict2obj, self).__init__(dict_)
        for key in self:
            item = self[key]
            if isinstance(item, list):
                for idx, it in enumerate(item):
                    if isinstance(it, dict):
                        item[idx] = dict2obj(it)
            elif isinstance(item, dict):
                self[key] = dict2obj(item)

    def __getattr__(self, key):
        # Enhanced to handle key not found.
        if self.has_key(key):
            return self[key]
        else:
            return None



class Struct(dict):
  def __init__(self,data):
    for key, value in data.items():
      if isinstance(value, dict):
        setattr(self, key, Struct(value))
      else:
        setattr(self, key, type(value).__init__(value))

      dict.__init__(self,data)

"""
 Helper function
 http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
 work around json unicode-utf8 and python-2.x string conversion
"""
def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

"""
 Helper function
 http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-of-unicode-ones-from-json-in-python
 work around json unicode-utf8 and python-2.x string conversion
"""
def _decode_dict(data):
    rv = {}
    for key, value in data.items():  # Py3   Py2: iteritems():
        if isinstance(key, unicode):
           key = key.encode('utf-8')
        if isinstance(value, unicode):
           value = value.encode('utf-8')
        elif isinstance(value, list):
             value = _decode_list(value)
        elif isinstance(value, dict):
             value = _decode_dict(value)
        rv[key] = value
    return rv



class JuMEG_Template(JuMEG_Base_Basic):
    def __init__ (self,template_name='DEFAULT'):
        super().__init__()

        self._template_path     = "123"#None  # os.getenv('JUMEG_PATH_TEMPLATE',self.__JUMEG_PATH_TEMPLATE)
        self._template_name     = template_name
        self._template_list     = []
        self._template_name_list= []
        self._template_postfix  = "template"
        self._template_suffix   = '.json'
        self._template_dic      = {}
        self._template_data     = dict()
        self._verbose           = False
        self._template_isUpdate = False

        self._template_path = self.template_path_default
        self.template_update_name_list()
        
   #--- temp path
    @property
    def template_path(self):   return self._template_path
    @template_path.setter
    def template_path(self,v): self._template_path = v
   #--- tmp path default
    @property
    def template_path_default(self): return os.path.abspath( os.path.dirname(__file__) ) + '/../examples/templates'
   #--- tmp name
    @property
    def template_name(self):   return self._template_name
    @template_name.setter
    def template_name(self,v): self._template_name = v
   #--- tmp data
    @property
    def template_data(self):   return  self._template_data
    @template_data.setter
    def template_data(self,v): self._template_data = v
   #--- template_postfix
    @property
    def template_postfix(self):   return self._template_postfix
    @template_postfix.setter
    def template_postfix(self,v): self._template_postfix = v
   #--- template_suffix
    @property
    def template_suffix(self):    return  self._template_suffix
    @template_suffix.setter
    def template_suffix(self,v):  self._template_suffix = v
   #---template_isUpdate
    @property
    def template_isUpdate(self): return self._template_isUpdate
   #--- template_name_lis
    @property
    def template_name_list(self): return self._template_name_list
    @template_name_list.setter
    def template_name_list(self,v): self._template_name_list = v
   #---template_filename
    @property
    def template_filename(self): return self.template_name + "_" + self.template_postfix + self.template_suffix
   #--- template_full_filename
    @property
    def template_full_filename(self): return self.template_path + '/' + self.template_filename

    #---
    def template_get_name_from_list(*args):
        if type( args[1] ) == int :
           return args[0]._template_name_list[ args[1] ]  # self = args[0]
        else :
           return args[0]._template_name_list
   #---
    def template_update_name_list(self):
         """ read experiment template dir & update experiment names
         Result
         ------
          template_name_list
         """
         self.template_name_list = []

         flist = glob.glob( self.template_path + '/*' + self.template_postfix + self.template_suffix)
         pat   = re.compile( (self.template_path + '|/|'+ '_' + self.template_postfix + self.template_suffix) )
         self.template_name_list = pat.sub('', str.join(',',flist) ).split(',')
        #---
         self.template_data = dict()
         return self.template_name_list

    def template_update_file(self):
          self._template_isUpdate = False

          try:
              with open(self.template_full_filename) as FH: # PY3
                   self.template_data = json.load(FH) # close  anyway

              self.template_data = dict2obj(self.template_data)
              self._template_isUpdate = True
          except ValueError as e:
              print("\n---> ERROR loading Template File: " + self.template_full_filename, file=sys.stderr)
              print(' --> invalid json: %s' % e, file=sys.stderr)

          assert self.template_data,"---> ERROR in template file format [json]\n"  
          return 
          
    def template_get_as_obj(self):
        return dict2obj( self.template_data )
    
    def template_update_and_merge_dict(self, d, u, depth=-1):
        """ update and merge template parameter overwrite defaults
        
        Parameters
        ----------
        dict with defaults parameter
        dict with parameter to merge or update
        depth: recusive level <-1>
                
        Result
        -------
        dict with merged and updated parameters
        
        Example
        -------
        copy from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        
        Recursively merge or update dict-like objects. 
        >>> update({'k1': {'k2': 2}}, {'k1': {'k2': {'k3': 3}}, 'k4': 4})
        {'k1': {'k2': {'k3': 3}}, 'k4': 4}
        return dict
        """
        import collections
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping) and not depth == 0:
               r = self.template_update_and_merge_dict(d.get(k, {}), v, depth=max(depth - 1, -1))
               d[k] = r
            elif isinstance(d, collections.Mapping):
               d[k] = u[k]
            else:
               d = {k: u[k]}
        
        return d

    def template_update_and_merge_obj(self, d, u, depth=-1):
        """
        copy from:
        http://stackoverflow.com/questions/3232943/update-value-of-a-nested-dictionary-of-varying-depth
        
        Recursively merge or update dict-like objects. 
        >>> update({'k1': {'k2': 2}}, {'k1': {'k2': {'k3': 3}}, 'k4': 4})
        {'k1': {'k2': {'k3': 3}}, 'k4': 4}
        return new object updated and merged
        """
        return dict2obj(self._dict_update_and_merge(d, u, depth=depth) )

    def template_read_json(self,fjson):
        d = dict()
        if ( os.path.isfile( fjson ) ):
            FID = open( fjson )
            try:
                d = json.load(FID)
                d = _decode_dict(d)
            except:
                d = dict()
                print("\n\n!!! ERROR NO JSON File Format:\n  ---> " + fjson,file=sys.stderr)
                print("\n\n",file=sys.stderr)
            FID.close()
        return d
        
    def template_write_json(self,fjson, d):
        with open(fjson, 'wb') as FOUT:
             json.dump(d,FOUT, sort_keys=True)   
             FOUT.close()

class JuMEG_Template_Experiments(JuMEG_Template):
    """
    class to work with <jumeg experiment templates>
    overwrite _init(**kwargs) for you settings

    Example
    -------
     from jumeg.template.jumeg_template import JuMEG_Template_Experiments

     class JuMEG_ExpTemplate(JuMEG_Template_Experiments):
        def __init__(self,**kwargs):
            super().__init__()

        def update_from_kwargs(self,**kwargs):
           self.template_path = kwargs.get("template_path",self.template_path)

        def _init(self,**kwargs):
            self.update_from_kwargs(**kwargs)

     TMP = JuMEG_ExpTemplate()
     print(TMP.template_path)

    """
    def __init__ (self,**kwargs):
        super().__init__()
        self.template_path    = os.getenv('JUMEG_PATH_TEMPLATE_EXPERIMENTS',self.template_path_default + '/jumeg_experiments')
        self.template_name    = 'default'
        self.template_postfix = 'jumeg_experiment_template'
        self._init(**kwargs)

    def _init(self,**kwargs):
        pass

experiment = JuMEG_Template_Experiments()
