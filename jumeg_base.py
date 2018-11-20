# -*- coding: utf-8 -*-

'''
JuMEG Base Class to provide wrapper & helper functions

Authors: 
         Prank Boers     <f.boers@fz-juelich.de>
         Praveen Sripad  <praveen.sripad@rwth-aachen.de>
License: BSD 3 clause

---> update 23.06.2016 FB

---> update 20.12.2016 FB
 --> add eeg pick-cls
 --> eeg BrainVision IO support

---> update 23.12.2016 FB
 --> add opt feeg in get_filename_list_from_file
 --> to merge eeg BrainVision with meg in jumeg_processing_batch

---> update 04.01.2017 FB
 --> add neww CLS JuMEG_Base_FIF_IO
 --> to merge eeg BrainVision with meg in jumeg_processing_batch

---> update 05.09.2017 FB
 --> update get_empty_room_fif
 --> use CLS function to read <empty room fif file> instead of mne.io stuff
 
---> update 05.04.2018 FB
 --> update JuMEG_Base_PickChannels.picks2label
 --> get lable list from index picks

---> update 13.04.2018 FB
 --> add pprint.PrettyPrinter(indent=4) as pp
  -> prints formated dict self.pp( my-dict)
 --> add line function
  -> prints line --- self.line()
---> update 05.07.2018 FB
 --> add update_bad_channels
  -> returns only unique bads
  
---> update 24.08.2018 FB
 --> update print()
  -> add isEmptyString,isNumber

'''

import os,sys,six
import numpy as np

# py3 obj from pathlib import Path

import warnings
with warnings.catch_warnings():
     warnings.filterwarnings("ignore",category=DeprecationWarning)
     import mne

from pprint import PrettyPrinter #,pprint,pformat
import logging

__version__= "2018.08.24.001"


'''
class AccessorType(type):
    """
    meta class example
    http://eli.thegreenplace.net/2011/08/14/python-metaclasses-by-example
    """
    def __init__(self, name, bases, d):
        type.__init__(self, name, bases, d)
        accessors = {}
        prefixs = ["__get_", "__set_", "__del_"]
        for k in d.keys():
            v = getattr(self, k)
            for i in range(3):
                if k.startswith(prefixs[i]):
                    accessors.setdefault(k[4:], [None, None, None])[i] = v
        for name, (getter, setter, deler) in accessors.items():
            # create default behaviours for the property - if we leave
            # the getter as None we won't be able to getattr, etc..

            # [...] some code that implements the above comment

            setattr(self, name, property(getter, setter, deler, ""))

'''

#-- logger
# https://docs.python.org/3/howto/logging-cookbook.html
# https://stackoverflow.com/questions/44522676/including-the-current-method-name-when-printing-in-python
def create_logger(app_name=None):
    logger = logging.getLogger(app_name or __name__)
    logger.setLevel(logging.DEBUG)
    log_format = '[%(asctime)-15s] [%(levelname)08s] (%(funcName)s %(message)s'
    logging.basicConfig(format=log_format)
    return logger


class bcolors:
    """
    cls for printing in colors
    https://stackoverflow.com/questions/287871/print-in-terminal-with-colors
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    

class JuMEG_Base_Basic(object):
    def __init__ (self):
        super(JuMEG_Base_Basic, self).__init__()

        self._verbose       = False
        self._debug         = False
        self._template_name = None
        self._do_run        = False
        self._do_save       = False
        self._do_plot       = False

        self._pp = PrettyPrinter(indent=4)
        self.logger = create_logger()

    @property
    def python_version(self):
        self.line()
        print("---> python sys version: " + sys.version_info)
        #try:
        #   print("---> wx version: " + wx.version)   
        #except:
        #   pass
        self.line()      
        return sys.version_info
    
    @property    
    def version(self): return __version__
    
    @property
    def verbose(self):  return self._verbose
    @verbose.setter
    def verbose(self,v):self._verbose=v
    
    @property
    def debug(self): return self._debug
    @debug.setter
    def debug(self,v):
        self._debug = v
        if self._debug:
           self.verbose =True

    @property
    def run(self):   return self._do_run
    @run.setter
    def run(self,v): self._do_run=v
    
    @property
    def save(self): return self._do_save
    @save.setter 
    def save(self,v): self._do_save=v
    
    @property
    def plot(self): return self._do_plot
    @plot.setter
    def plot(self,v): self._do_plot=v   
    
    def print_warning(self,msg,head=None):
        """
        print warning msg in green
        
        Parameters
        ----------
        msg : strig
        head: like title <None>
        """
        print( bcolors.WARNING)
        self.line(char="*")
        if head: print(head)
        print( msg )
        self.line(char="*")
        print(bcolors.ENDC)
            
    def print_error(self,msg,head=None,file=sys.stderr):
        """
        print error msg in red 
        
        Parameters
        ----------
        msg : strig
        head: like title <None>
        """
        print(bcolors.ERROR + bcolors.BOLD,file=file)
        self.line(char="! . ",n=10,file=file)
        if head: print(head,file=file)
        print( msg,file=file )
        self.line(char=". ! ",n=10,file=file)
        print(bcolors.ENDC,file=file)
    
    def line(self,n=40,char="-",file=None):
        """ line: prints a line for nice printing  and separate
        Parameters:
        -----------
        n   : factor to print n x times character <n=50>
        char: character to print n x times        <"-">
        file: <sys.stdout>
        Returns:
        ----------
        print a seperator line 
        
        Example:
        ---------
        from jumeg.jumeg_base import jumeg_base as jb   
        jb.line()
        --------------------------------------------------
        
        jb.line(n=10,char="x")
        xxxxxxxxxx
        """
        if file:
            print(char * n, file=file)
        else:
            print(char * n)

    def pp_list2str(self,param,head=None):
        """
        Parameter
        ---------
         dict,string

        Result
        -------
         pretty formated string
        """
        if isinstance(param,(dict,list)):
           if head:
              return head+"\n" + ''.join(map(str,self._pp.pformat(param)))
           return ''.join(map(str,self._pp.pformat(param)))
        if head:
           return head+"\n" + self._pp.pformat(param)
        return self._pp.pformat(param)

    def pp(self,param,head=None,l1=True,l2=True,n=50,char="-",file=None):
        """
        prints pretty formated dictonary
        
        Parameters
        ----------
        param : obj
                dictionary or data frame
        
        head  : string [None]
                print headline
        l1    : bool [True]
                print line at first line
        l2    : bool [True]
                print line at the end
        n     : factor to print n x times character <n=50>
        char  : character to print n x times        <"-">
        file  : <sys.stdout>

        Returns
        -------
        print out dictionary in terminal
        
        Examples
        --------
        from jumeg.jumeg_base import jumeg_base as jb 
        
        param={"A":"Atest","AA":{"test1":"Hello","test2":"World"},
               "B":"Btest","BB":{"test1":"Hello","test2":"Space"}}
        jb.pp( param,head="HelloWorld")
        
        """
        if l1  : self.line(n=n,char=char,file=file)
        if head: print(head,file=file)
        
        # self._pp.pprint(param)
        for line in self._pp.pformat(param).split('\n'):
            print(line,file=file)

        if l2  : self.line(n=n,char=char,file=file)
        print("",flush=True,file=file)
        
    def is_number(self,n):
        """ 
        check if input is a number:  isinstance of int or float
         no check for numpy ndarray
        
        Parameters:
        ------------            
        n: value to check
        
        Returns:
        ---------
        True / False
        
        Example
        ---------
        from jumeg.jumeg_base import jumeg_base as jb  
        
        jb.is_number(123)
         True
        """
        return isinstance(n,(int, float) )
 
    def isNumber(self,n):
        """
         wrapper fct. call <is_number>
        """
        return self.is_number(n)
    
    def isNotEmptyString(self,s):
        """
         check not empty string
         https://stackoverflow.com/questions/4843173/how-to-check-if-type-of-a-variable-is-string
        """
        if not s : return
        if isinstance(s,six.string_types): return bool(s.strip())
        # PY2 if isinstance(s, basestring): return bool(s.strip())
        return False
    
    def isNotEmpty(self,v):
        """
         check not empty string,int,float,list,tuple types
         not for numpy arrays
         https://stackoverflow.com/questions/4843173/how-to-check-if-type-of-a-variable-is-string
         
         no check for numpy ndarray
        """
        if isinstance( v,(int,float,list,tuple) ): return True
        if self.is_number(v):                      return True
        if isinstance(v,six.string_types):         return bool(v.strip())
        
        # PY2 if isinstance(s, basestring): return bool(s.strip())
        return False
    
    def isFile(self,fin,head="ERROR JuMEG_Base_Basic:isFile"):
        """
        check if file exist

        Parameters
        ----------
        string: full filename to check

        Result
        ------
        abs full file name/False
        """
        f = os.path.abspath( os.path.expandvars( os.path.expanduser(fin) ) )
        if os.path.isfile( f ):
           return f
        self.print_error("\n".join([" --> no such file or directory: " +fin,"  -> abs file{:>18} {}".format(':',f)]),
                         head=head)
        return False

    def isPath(self,pin,head="ERROR JuMEG_Base_Basic:isPath",print_error=True):
        """
        check if file exist
        use os.path.isdir: very slow

        Parameters
        ----------
         string: full filename to check
         print_error : prints error MSG to sys.stderr [slow] <True>

        Result
        ------
        abs full path/False
        """
        p = os.path.abspath( os.path.expandvars( os.path.expanduser(pin) ) )
        if os.path.isdir( p ):
           return p
        if not print_error: return
        self.print_error("\n".join([" --> no such path or directory: " +pin,"  -> abs path{:>18} {}".format(':',p)]),head=head)
        return False

class JuMEG_Base_PickChannels(object):
    """ MNE Wrapper Class for mne.pick_types
    return list of channel index from mne.raw obj e.g. for special groups
        
    Wrapper call to    
     --> mne.pick_types(raw.info, **fiobj.pick_all) 
     --> mne.pick_types(info, meg=True, eeg=False, stim=False, eog=False, ecg=False, emg=False, ref_meg='auto',
                           misc=False, resp=False, chpi=False, exci=False, ias=False, syst=False,
                           include=[], exclude='bads', selection=None)

    https://github.com/mne-tools/mne-python/blob/master/mne/io/pick.py  lines 20ff
    type : 'grad' | 'mag' | 'eeg' | 'stim' | 'eog' | 'emg' | 'ecg' |'ref_meg' | 'resp' | 'exci' | 'ias' | 'syst' | 'misc'|'seeg' | 'chpi'  
     
    Example:
    ---------   
    from jumeg.jumeg_base import jumeg_base as jb  
        
    jb.picks.meg( raw )
    return meg channel index array => 4D Magnes3600 => [0 .. 247]
         
    jb.picks.meg_nobads( raw )
    return meg channel index array without bad channels
       
    extended function:
    jb.picks.picks2labels(raw,picks)
         
    jb.picks.labels2picks(raw,labels)
         
    #---- 
    or only import this class
    from jumeg.jumeg_base import JuMEG_Base_PickChannels
         
    picks = JuMEG_Base_PickChannels()
    picks.meg_nobads( raw ) 
    """  
      
    def __init__ (self):
        """ init """
        # getting from <mne.pick_types>
        #self._pick_type_set={'meg','mag', 'grad', 'planar1','planar2','eeg','stim','eog','ecg','emg','ref_meg','misc',
        #                     'resp','chpi','exci','ias','syst','seeg','dipole','gof','bio','ecog','fnirs'}

       #--- mne version 0.17
        self._pick_type_set={'eeg', 'mag', 'grad', 'ref_meg', 'misc', 'stim', 'eog', 'ecg', 'emg', 'seeg', 'bio', 'ecog', 'hbo', 'hbr'}

    @property
    def pick_type_set(self): return self._pick_type_set

    def picks2labels(self,raw,picks):
        """ get channel labels from picks
        Parameter
        ---------
         raw obj
         picks as numpy array int64

        Result
        -------
         return label list
        """
        if isinstance(picks,(int)):
           return raw.ch_names[picks] 
        return ([raw.ch_names[i] for i in picks]) 
       
    def labels2picks(self,raw,labels):
        """
        get picks from channel labels
        call to < mne.pick_channels >
        picks = mne.pick_channels(raw.info['ch_names'], include=[labels])

        Parameter
        ---------
         raw obj
         channel label or list of labels

        Result
        -------
         picks as numpy array int64
        """
        if isinstance(labels,(list)):
           return  mne.pick_channels(raw.info['ch_names'],include=labels)
        else:
           return mne.pick_channels(raw.info['ch_names'],include=[labels])

    def channels(self,raw):
        """ call with meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False,exclude=None """
        return mne.pick_types(raw.info,meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False,exclude=[])  
     
    def channels_nobads(self, raw):
        """ call with meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False,exclude='bads' """
        return mne.pick_types(raw.info, meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False,exclude='bads')
       
    def all(self, raw):
        """ call with meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True, stim=True,resp=True,exclude=None """
        return mne.pick_types(raw.info, meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True, stim=True,resp=True,exclude=[])       
    
    def all_nobads(self, raw):
        """ call with meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True, stim=True,resp=True,exclude='bads' """
        return mne.pick_types(raw.info, meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True, stim=True,resp=True,exclude='bads')
       
    def meg(self,raw):
        """ call with meg=True """
        return mne.pick_types(raw.info,meg=True)      
    
    def meg_nobads(self,raw):
        ''' call with meg=True,exclude='bads' '''
        return mne.pick_types(raw.info, meg=True,exclude='bads')
    
    def ref(self,raw):
        ''' call with ref=True'''
        return mne.pick_types(raw.info,ref_meg=True,meg=False,eeg=False,stim=False,eog=False)
    def ref_nobads(self,raw):
        ''' call with ref=True,exclude='bads' '''
        return mne.pick_types(raw.info,ref_meg=True,meg=False,eeg=False,stim=False,eog=False,exclude='bads')
        
    def meg_and_ref(self,raw):
        ''' call with meg=True,ref_meg=True'''
        return mne.pick_types(raw.info, meg=True,ref_meg=True, eeg=False, stim=False,eog=False)
    def meg_and_ref_nobads(self,raw):
        ''' call with meg=mag,ref_meg=True,exclude='bads' '''
        return mne.pick_types(raw.info,meg=True,ref_meg=True,eeg=False,stim=False,eog=False,exclude='bads')
  
    def meg_ecg_eog_stim(self,raw):
        ''' call with meg=True,ref_meg=False,ecg=True,eog=Truestim=True,'''
        return mne.pick_types(raw.info, meg=True,ref_meg=False,eeg=False,stim=True,eog=True,ecg=True)
    def meg_ecg_eog_stim_nobads(self,raw):
        ''' call with meg=True,ref_meg=False,ecg=True,eog=True,stim=True,exclude=bads'''
        return mne.pick_types(raw.info, meg=True,ref_meg=False,eeg=False,stim=True,eog=True,ecg=True,exclude='bads')
       
    def ecg(self,raw):
        ''' meg=False,ref_meg=False,ecg=True,eog=False '''
        return mne.pick_types(raw.info,meg=False,ref_meg=False,ecg=True,eog=False)
    def eog(self,raw):
        ''' meg=False,ref_meg=False,ecg=False,eog=True '''
        return mne.pick_types(raw.info,meg=False,ref_meg=False,ecg=False,eog=True)
   
    def ecg_eog(self,raw):
        ''' meg=False,ref_meg=False,ecg=True,eog=True '''
        return mne.pick_types(raw.info,meg=False,ref_meg=False,ecg=True,eog=True)

    def eeg(self,raw):
        ''' meg=False,ref_meg=False,ecg=False,eog=False '''
        return mne.pick_types(raw.info,meg=False,ref_meg=False,ecg=False,eog=False,eeg=True)
    def eeg_nobads(self, raw):
        ''' meg=False,ref_meg=False,ecg=False,eog=False '''
        return mne.pick_types(raw.info, meg=False, ref_meg=False, ecg=False, eog=False, eeg=True, exclude='bads')

    def eeg_ecg_eog(self, raw):
        ''' meg=False,ref_meg=False,ecg=True,eog=True,eeg=True '''
        return mne.pick_types(raw.info, meg=False, ref_meg=False, ecg=True, eog=True, eeg=True)
    def eeg_ecg_eog_nobads(self, raw):
        ''' meg=False,ref_meg=False,ecg=True,eog=True,eeg=True '''
        return mne.pick_types(raw.info, meg=False, ref_meg=False, ecg=True, eog=True, eeg=True, exclude='bads')

    def stim(self,raw):
        ''' call with meg=False,stim=True '''
        return mne.pick_types(raw.info,meg=False,stim=True)
        
    def response(self,raw):
        ''' call with meg=False,resp=True'''
        return mne.pick_types(raw.info,meg=False,resp=True)
        
    def stim_response(self,raw):
        ''' call with meg=False,stim=True,resp=True'''
        return mne.pick_types(raw.info, meg=False,stim=True,resp=True)

    def stim_response_ecg_eog(self,raw):
        ''' call with meg=False,stim=True,resp=True'''
        return mne.pick_types(raw.info, meg=False,stim=True,resp=True,ecg=True,eog=True)

    def exclude_trigger(self, raw):
        ''' call with meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False,exclude=None '''
        return mne.pick_types(raw.info, meg=True,ref_meg=True,eeg=True,ecg=True,eog=True,emg=True,misc=True,stim=False,resp=False)       

    def bads(self,raw):
        """ return raw.info[bads] """
        return raw.info['bads']

class JuMEG_Base_StringHelper(JuMEG_Base_Basic):
    """ Helper Class to work with strings """
    
    def __init__ (self):
        super(JuMEG_Base_StringHelper,self).__init__()
         
    def isString(self, s):
        """ check if is string return True/False
         http://ideone.com/uB4Kdc
        
        Example
        -------- 
        from jumeg.jumeg_base import jumeg_base as jb  
        
        jb.isString("Hell World")
         True
         
        """
        if not s: return False
        if (isinstance(s, str)):
           return True
        try:
           if (isinstance(s, basestring)):
              return True
        except NameError:
           return False
        
        return False    

    def isNotEmptyString(self,s):
        '''
        check if is value is a string and not empty
         e.g. s=""  
        
         Parameter
         ---------
          value to check
         
         Results
         -------
          True/False
         
          http://ideone.com/uB4Kdc
        
        Example
        -------- 
        from jumeg.jumeg_base import jumeg_base as jb  
        
        s="" 
        jb.isEmptyString(s)
        >> False
         
        '''
        if self.isString(s):
           if s.strip(): return True
        return False
         
    def str_range_to_list(self, seq_str):
        """make a list of inergers from string
        ref:
        http://stackoverflow.com/questions/6405208/how-to-convert-numeric-string-ranges-to-a-list-in-python
           
        Parameters
        ----------
        seq_str: string
        
        Returns
        --------
        list of numbers
        
        Example
        --------
        from jumeg.jumeg_base import jumeg_base as jb 
        
        jb.str_range_to_list("1,2,3-6,8,111")
        
        "1,3,5"         => [1,3,5]
        "1-5"           => [1,2,3,4,5]
        "1,2,3-6,8,111" => [1,2,3,4,5,6,8,111]
        """
        xranges = [(lambda l: xrange(l[0], l[-1]+1))(map(int, r.split('-'))) for r in seq_str.split(',')]
         # flatten list of xranges
        return [y for x in xranges for y in x]
      
    def str_range_to_numpy(self, seq_str,exclude_zero=False,unique=False): 
        """converts integer string to numpy array 
        Parameters
        ----------
        input       : integer numbers as string
        exclude_zero: exclude 0  <False>
        unique      : return only unique numbers <False>
        
        Returns
        --------
        integer numbers as numpy array dtype('int64')
        
        Example
        --------
        
        from jumeg.jumeg_base import jumeg_base as jb 
        
        s = "0,1,2,3,0,1,4,3,0"
        
        jb.str_range_to_numpy(s)
          array([0, 1, 2, 3, 0, 1, 4, 3, 0])
        
        jb.str_range_to_numpy(s,unique=True)
          array([0, 1, 2, 3, 4])
              
        jb.str_range_to_numpy(s,exclude_zero=True)
          array([1, 2, 3, 1, 4, 3])
        
        jb.str_range_to_numpy(s,unique=True,exclude_zero=True)
          array([1, 2, 3, 4]) 
           
        """
        import numpy as np

        if seq_str is None:
           return np.unique( np.asarray( [ ] ) )
        if self.isString(seq_str):
           anr = np.asarray (self.str_range_to_list( seq_str ) )
        else:
           anr = np.asarray( [seq_str] )
           
        if unique:
           anr = np.unique( anr ) 
        if exclude_zero:
           return anr[ np.where(anr) ] 
        return anr

class JuMEG_Base_FIF_IO(JuMEG_Base_StringHelper):
    """ handels mne fif I/O for meg and eeg [BrainVision] data
        workaround to manage different MNE versions
        
    """
    def __init__ (self):
        super(JuMEG_Base_FIF_IO, self).__init__()
        
    def set_raw_filename(self,raw,v):
        """ set filename in raw obj"
        Parameters:
        -----------
        raw     : rawobj to modify
        filename: filename
        
        Returns:
        ----------
        None
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
         
        jb.set_raw_filename(raw,"/data/test-raw.fif")
        """
        if hasattr(raw,"filenames"):
           raw._filenames = []
           raw._filenames.append(v)
        else:
           raw.info['filename'] = v


    def get_raw_filename(self,raw,index=0):
        """ get filename from raw obj
        
        Parameters:
        -----------
        raw     : raw-obj to modify
        index   : index in list of filenames from raw.filenames <0>      
                  if index = list return filename list
        Returns:
        ----------
         first filename or None
        
        Example:
        ----------
         from jumeg.jumeg_base import jumeg_base as jb 
         fname = jb.get_raw_filename(raw)
        """
        if raw:
           if hasattr(raw,"filenames"): 
              if index == "list"                : return raw.filenames 
              if abs(index) < len(raw.filenames): return raw.filenames[index]
              return raw.filenames
           return raw.info.get('filename')
        return None 
    
    def __get_from_fifname(self,v=None,f=None):
        try:
           return os.path.basename(f).split('_')[v]
        except:
           return os.path.basename(f)

    def get_id(self,v=0,f=None):
        """ get id from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        subject id in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_id(f=f)
        "211776"
        
        """
        return self.__get_from_fifname(v=v,f=f)

    def get_scan(self,v=1,f=None):
        """ get scan from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        scan in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_scan(f=f)
        "FREEVIEW01"
        """
        return self.__get_from_fifname(v=v,f=f)
    
    def get_date(self,v=2,f=None):
        """ get session from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        date in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_session(f=f)
        "180115"
        """
        return self.__get_from_fifname(v=v,f=f)

    def get_time(self,v=3,f=None):
        """ get time from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        time in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_run(f=f)
        "1414"
        """
        return self.__get_from_fifname(v=v,f=f)
    
    def get_session(self,f=None):
        """ get session from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        session in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_session(f=f)
        "180115_1414"
        """
        return self.get_date(f=f)+"_"+self.get_time(f=f)
      
    def get_run(self,v=4,f=None):
        """ get run from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        run in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_run(f=f)
        "1"
        """
        return self.__get_from_fifname(v=v,f=f)

    def get_postfix(self,f=None):
        """ get postfix from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        postfix in fif filename
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_postfix(f=f)
        "bcc,tr,nr,ar-raw"
        
        """
        return os.path.basename(f).split('_')[-1].split('.')[0]

    def get_extention(self,f=None):
        """ get extention from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        file extention in fif filename  <fif>; without leading <.>
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_extention(f=f)
        "fif"
       
        """
        if f:
            fname = f
        else:
            fname = self.raw.info['filename']
        return os.path.basename(fname).split('_')[-1].split('.')[-1]

    def get_postfix_extention(self,f=None):
        """ get postfix with extention from fifname 
        
        Parameters:
        -----------
        f  : filename <None>
        
        Returns:
        ----------
        postfix with extention in fif filename 
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        f='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        
        jb.get_postfix_extention(f=f)
        "bcc,tr,nr,ar-raw.fif"
        """
        if f:
            fname = f
        else:
            fname = self.raw.info['filename']
        return os.path.basename(fname).split('_')[-1]
   

class JuMEG_Base_IO(JuMEG_Base_FIF_IO):
    """I/O class to handle higher order work on raw obj
       e.g.: read in raw obj from meg, eeg or ica data
             update bad channels
    """
    def __init__ (self):
        super(JuMEG_Base_IO, self).__init__()
        
        self.picks = JuMEG_Base_PickChannels()

      #--- ToDo --- start implementig BV support may new CLS
        self.brainvision_response_shift = 1000
        self.brainvision_extention      = '.vhdr'
        
    def get_fif_name(self, fname=None, raw=None, prefix=None,postfix=None, extention="-raw.fif", update_raw_fname=False):
        """
        changing filename with prefix postfix and option to update filename in raw-obj
        
        Parameters:
        -----------
        fname            : base file name
        raw              : raw obj, if defined get filename from raw obj                <None>
        prefix           : string to add as prefix in filename                          <None>
        postfix          : string to add as postfix for applied operation               <None>
        extention        : string to add as extention                                   <-raw.fif>
        update_raw_fname : if true and raw is obj will update raw obj filename in place <False>
       
        Returns:
        ----------
        fif filename, based on input file name and applied operation
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        
        f ='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        raw,fraw=jb.get_raw_obj(f)
        
        jb.get_fif_name(raw=raw)
        "/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif"
        
        jb.get_fif_name(raw=raw,prefix="PREFIX",postfix="POSTFIX")

        """
        if raw:
           fname = self.get_raw_filename(raw)

           p, pdf = os.path.split(fname)
           fname = p + "/" + pdf[:pdf.rfind('-')]
           if prefix:
              fname = prefix +","+ fname
           if postfix:
              fname += "," + postfix
              fname = fname.replace(',-', '-')
           if extention:
              fname += extention
           if update_raw_fname:
               self.set_raw_filename(raw,fname)
        return fname
        
    def update_bad_channels(self,fname,raw=None,bads=None,preload=True,append=False,save=False,interpolate=False,postfix=None):
        """ update bad channels in raw obj
        
        Parameters:
        -----------
        fname   : file name
        raw     : raw obj, if defined get filename from raw obj <None>
        bads    : list of bad channels                          <None> 
        postfix : add postfix to filename                       <None>
        
        Flags:
         preload : mne loar flag                                <True>
         append  : add bads to bads if true or overwrite        <False>
         postfix : add postfix to filename                      <None>
         save    : will raw with changes in bads                <False>
         interpolate: apply mne badchannel interpolation        <False>
         
        Returns:
        ----------
        return: raw, bad channel list        
        
        Example:
        ----------
        from jumeg.jumeg_base import jumeg_base as jb 
        
        f  ='/data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar-raw.fif'
        bads=["MEG 010","MEG 157"] or bads="MEG 010,MEG 157"
        raw,bads_list = jb.update_bad_channels(f,raw=raw,postfix="bads",save=True,bads=bads)
        
        saved bads as new fif file:
        /data/exp/FREEVIEWING/epocher/211776_FREEVIEW01_180115_1414_1_c,rfDC,meeg_bcc,tr,nr,ar,bads-raw.fif
        
        """
        #TODO: if  new bads ==  old bads in raw then  exit
   
        if save:
           preload = True
        raw,fname = self.get_raw_obj(fname,raw=raw,preload=preload)

        if not append:
           raw.info['bads']=[]

        if not isinstance(bads,list):
           bads = bads.split(',')

        if not bads:
           if not append:
              raw.info['bads']=[]
        else:
           for b in bads:
               bad_ch = None
               if (b in raw.ch_names):
                  bad_ch = b
               else:
                  if b.startswith('A'):
                     bad_ch = 'MEG '+ b.replace(" ","").strip('A').zfill(3)
                  elif b.startswith('MEG'):
                     bad_ch = 'MEG '+ b.replace(" ","").strip('MEG').zfill(3)
               if bad_ch:
                  if bad_ch not in raw.info['bads']:
                     raw.info['bads'].append(bad_ch)
        
     #--- only unique channel names sorted
        if raw.info['bads']:
           b = list( set( raw.info['bads'] ) )
           b.sort() # inplace !!!
           raw.info['bads'] = b
        
        fif_out = self.get_fif_name(raw=raw,postfix=postfix)

        if self.verbose:
           print("\n --> Update bad-channels")
           print(" --> FIF in  :" + self.get_raw_filename(raw))
           print(" --> FIF out :" + fif_out)
           print(raw.info['bads'])
           print("\n")
              
        if ( interpolate and raw.info['bads'] ) :
           print(" --> Update BAD channels => interpolating: " + raw.info['filename'])
           print(" --> BADs : ") 
           print(raw.info['bads']) 
           print("\n\n")
           raw.interpolate_bads()
     
      #--- save raw as bads-raw.fif
        if save:
           raw.save( fif_out,overwrite=True)
        self.set_raw_filename(raw,fif_out)
             
        return raw,raw.info['bads']

#--- helper function
    def get_ica_raw_obj(self,fname_ica,ica_raw=None):
        """check for <ica filename> or <ica raw obj>
        if <ica_raw> obj is None load <ica raw obj> from <ica filename>

        Parameters:
        -----------  
        fname_ica: ica filename 
        raw_ica  : ica raw obj <None> 
        
        Returns:
        --------
        <ica raw obj>,ica raw obj filename
        
        """
        if ica_raw is None:
           if fname_ica is None:
              assert "---> ERROR no file foumd!!\n\n"
              if self.verbose:
                 print("<<<< Reading ica raw data ...")
        
           ica_raw = mne.preprocessing.read_ica(fname_ica)
         
           if ica_raw is None:
              assert "---> ERROR in jumeg.jumeg_base.get_ica_raw_obj => could not get ica raw obj:\n ---> FIF name: " + fname_ica   
   
        return ica_raw,self.get_raw_filename(ica_raw)
            
    def get_raw_obj(self,fname_raw,raw=None,path=None,preload=True):
        """
        load file in fif format <*.raw> or brainvision eeg data
        check for filename or raw obj
        check for meg or brainvision eeg data *.vhdr
        if filename -> load fif file
        
        Parameters
        ----------
         fname_raw: name of raw-file 
         raw      : raw obj <None>
        
        Results
        ----------
         raw obj
         fname from raw obj 
        """
        if raw is None:
           assert(fname_raw),"---> ERROR no file foumd!!\n"
           if self.verbose:
              print("<<<< Reading raw data ...")
           fn = fname_raw
           if path:
              fn = path+"/"+fname_raw
           if ( fn.endswith(self.brainvision_extention) ):
               raw = mne.io.read_raw_brainvision(fn,response_trig_shift=self.brainvision_response_shift,preload=preload)
               raw.info['bads'] = []
               #--- ToDo may decide for eeg-name .eeg or.vhdr
           else:
               raw = mne.io.Raw(fn,preload=preload)
       
        assert(raw), "---> ERROR in jumeg.jumeg_base.get_raw_obj => could not get raw obj:\n ---> FIF name: " + fname_raw
   
        return raw,self.get_raw_filename(raw)



    def get_files_from_list(self, fin):
        """ get filename or filenames from a list
        Parameters
        ----------
        filename or list of filenames
        
        Results
        -------
        files as iterables lists 
        """
        if isinstance(fin, list):
           fout = fin
        else:
           if isinstance(fin, str):
              fout = list([ fin ]) 
           else:
              fout = list( fin )
        return fout

    def get_filename_list_from_file(self, fin, start_path = None):
        """ loads filenames with options / parameter form a text file
        
        Parameters
        ----------
        fin       : text file to open
        start_path: start dir <None>
        
        Results
        --------
        list of existing files with full path and dict with bad-channels (as string e.g. A132,MEG199,MEG246)
        
        Example
        --------
        txt file format:
          
          fif-file-name  --feeg=myeeg.vhdr --bads=MEG1,MEG123 --startcode=123
          e.g.:
          0815/M100/121130_1306/1/0815_M100_121130_1306_1_c,rfDC-raw.fif --bads=A248
          0815/M100/120920_1253/1/0815_M100_120920_1253_1_c,rfDC-raw.fif
          0815/M100/130618_1347/1/0815_M100_130618_1347_1_c,rfDC-raw.fif --bads=A132,MEG199

        call with program:
        jumeg_merge_meeg -smeg /data/meg_stroe1/exp/INTEXT/eeg/INTEXT01/ -seeg /data/meg_stroe1/exp/INTEXT/mne/ -plist /data/meg_stroe1/exp/INTEXT/doc/ -flist 207006_merge_meeg.txt -sc 5 -b -v -r
         where -flist 207006_merge_meeg.txt is the text file
        """
        found_list = []
        # bads_dict  = dict()
        opt_dict = dict()
        
        assert os.path.isfile(fin),"ERROR no list-file found: %s" %( fin ) 
           
        try:
            fh = open( fin )
        except:
            assert "---> ERROR no such file list: " + fin
                
        for line in fh :
            line  = line.strip()
            fname = None
            if line :
               if ( line[0] == '#') : continue
               opt = line.split(' --')
               fname = opt[0].strip()
               if start_path :
                  if os.path.isfile( start_path + "/" + fname ):
                     fname = start_path + "/" + fname
               #print "Fname: "+fname

               if os.path.isfile( fname ):
                  found_list.append(fname)
                  #print "found Fname: "+fname
   
               opt_dict[fname]= {}
               for opi in opt[1:]:
                   opkey,opvalue=opi.split('=')
                   if opkey:
                      opt_dict[fname][ opkey.strip() ] = opvalue
                        
                        # if ('--bads' in opi):
                        #     _,opt_dict[fname]['bads'] = opi.split('--bads=')
                        # if ('--feeg' in opi):
                        #     _,opt_dict[fname]['feeg'] = opi.split('--feeg=')
        try:           
            fh.close()
        except:
            print("  -> UP`s error: can not close list-file:" +fin)
        
        if self.verbose :
           print(" --> INFO << get_filename_list_from_file >> Files found: %d" % ( len(found_list) ))
           print(found_list)
           print("\n --> BADs: ")
           print(opt_dict)
           print("\n")

        return found_list,opt_dict

    def add_channel(self,raw,ch_name=None,ch_type=None,data=None):
        """
        Adds a channel to raw obj, works in place.

        Parameters
        ----------
         mne.io.Raw obj
         ch_name : Name of the channel to add <None>
         ch_type : channel type from mne-type
                   e.g: get channel type from eeg raw-obj.info
                        channel_type = mne.io.pick.channel_type(eeg_raw.info,channel_idx )
         data    : channel data to add as numpy array <None>

        Returns
        -------
         mne.io.Raw obj with new channel
        """

        if ch_type not in self.picks.pick_type_set:
           ch_type='misc'

        picks = self.picks.labels2picks(raw, labels=ch_name)

        if not isinstance(data,np.ndarray):
           data = np.zeros(raw.n_times)

      #--- if channel does not exist add new channel
        if picks.shape[0] == 0:
           info = mne.create_info([ch_name],raw.info['sfreq'],[ch_type])
           if len(data.shape) < 2:
              ch_raw = mne.io.RawArray(data.reshape(1, -1),info)
           else:
              ch_raw = mne.io.RawArray(data,info)
           raw.add_channels([ch_raw],force_update_info=True)

        else: #--- if channel already exists copy data keep raw-channel-dtype:
           data.dtype = raw._data[ picks[0] ].dtype
           raw._data[picks[0],:] = data

          # channel_type = mne.io.pick.channel_type(raw.info, 75)

    def apply_save_mne_data(self,raw,fname="test.fif",overwrite=True):
        """saving mne raw obj to fif format
        
        Parameters
        ----------
        raw      : raw obj
        fname    : file name <None>
        overwrite: <True>
        
        Returns
        ----------
        filename
        """
        from distutils.dir_util import mkpath
         
        if ( os.path.isfile(fname) and ( not overwrite) ) :
           print(" --> File exist => skip saving data to : " + fname)
        else:
          print(">>>> writing filtered data to disk...")
          print(' --> saving: '+ fname)
          mkpath( os.path.dirname(fname) )
          raw.save(fname,overwrite=True)
          print(' --> Bads:' + str( raw.info['bads'] ))
          print(" --> Done writing data to disk...")
        
        return fname

    def get_empty_room_fif(self,fname=None,raw=None, preload=True):
        """find empty room file for input file name or RAWobj 
        assuming <empty room file> is the last recorded file for this id scan at this specific day
        e.g.: /data/mne/007/M100/131211_1300/1/1007_M100_131211_1300_1_c,rfDC-raw.fif
        search for id:007 scan:M100 date:13:12:11 and extention: <empty.fif>
        
        Parameters
        ----------
        raw    : raw obj
        fname  : file name <None>
        preload: will load and return empty-room-raw obj instead of raw <True>
        
        Returns
        ---------
        full empty room filename, empty-room-raw obj or raw depends on preload option
        """
        import glob

        fname_empty_room = None
       
        if raw is not None:
           fname = self.get_raw_filename(raw)
         #--- first trivial check if raw obj is the empty room obj   
           if fname.endswith('epmpty.fif'):
              return(fname,raw)
               
         #--- ck if fname is the empty-room fie  
        if fname.endswith('epmpty.fif'):
           fname_empty_room = fname  
         #--- ok more difficult lets start searching ..
        else : 
            # get path and pdf (in memory of 4D filenames) from filename
           p,pdf = os.path.split(fname)
            # get session dat from file
           session_date = pdf.split('_')[2]

            # get path to scan from p and pdf
           path_scan    = p.split( session_date )[0]
            #--- TODO: may check for the latest or earliest empty-room file
           try:
               fname_empty_room = glob.glob( path_scan + session_date +'*/*/*-empty.fif' )[0]
           except:
               print("---> ERROR can not find empty room file: " + path_scan + session_date)
               return

        if fname_empty_room and preload:
           if self.verbose:
              print("\n --> Empty Room FIF file found: %s \n" % (fname_empty_room))
           
           return self.get_raw_obj(fname_empty_room,raw=None,preload=True) # return raw,fname

           # return( fname_empty_room, mne.io.Raw(fname_empty_room, preload=True) )

   
#---
jumeg_base       = JuMEG_Base_IO()
jumeg_base_basic = JuMEG_Base_Basic()

