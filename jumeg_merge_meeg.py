#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Class JuMEG_MergeMEEG

Class to merge brainvision eeg data into MEG-fif file

Authors:
         Frank Boers     <f.boers@fz-juelich.de>
         Praveen Sripad  <praveen.sripad@rwth-aachen.de>
License: BSD 3 clause
----------------------------------------------------------------
merge ECG,EGO signals form BrainVision system into MEG-fif file
-> read meg raw fif
-> read bv eeg
-> find start events in raw and bv-eeg
-> lp-filter eeg and meg data
-> downsample eeg merge into meg-fif
-> adjust meg data size
-> save to disk [...eeg-raw.fif]

example via obj:
from jumeg.jumeg_merge_meeg import JuMEG_MergeMEEG
JMEEG = JuMEG_MergeMEEG()
JMEEG.meg_fname= my_meg_fname.fif
JMEEG.eeg_fname= my_eeg_fname.vhdr
JMEEG.run()

example  via function call
import jumeg.jumeg_merge_meeg
jumeg_merge_meeg(meg_fname= my_meg_fname.fif, eeg_fname = my_eeg_fname.vhdr)

---> update 09.01.2017 FB
     add cls for meg/eeg data
     error checking fix support for meg.raw
---> update 21.08.2017 FB
     update drift check function
---> update 19.10.2017 FB
     update drift check function
---> update 29.06.2018 FB
     update put get_argv into JuMEG_MergeMEEG class
     prepare for GUI interfacing via argparse
---> update 27.08.2018 FB
     print"" => print("") for py3
---> update 04.09.2018 FB
     new interface function apply_ jumeg_merge_meeg
     bugfix: can not set min_duratio
---> update 26.09.2018 FB
     changes to py3
     bugfix for handling old style eeg labeling: ECG EOG_hor EOG_ver
     in our 4D MEG Scan Parameter:
     old style :['EOG 001','ECG 001','EOG 002']
     new style :['EEG 001','EEG 001','EEG 002']
 ---> update 13.11.2018 FB
     add non existing channel to meg data, if channel is in eeg data but not in meg data

'''


import numpy as np

# import warnings
import os,sys,argparse

#--- https://stackoverflow.com/questions/40993553/unable-to-suppress-deprecation-warnings
import warnings
with warnings.catch_warnings():
     warnings.simplefilter("ignore", category=PendingDeprecationWarning)
     import mne

from jumeg.jumeg_base                   import JuMEG_Base_IO
from jumeg.jumeg_base                   import jumeg_base as jb
from jumeg.filter.jumeg_filter          import jumeg_filter


__version__= '2018.11.13.001'

class JuMEG_MergeMEEG_HiLoRate(object):
    """
    JuMEG_MergeMEEG_HiLoRate class for high and lwower sampled data e.g. meg and eeg data
    in JuMEG eeg brainvision data are sampled with 5kHz and meg with 4D sampling rates
    """
    def __init__(self, system='MEG'):
        super(JuMEG_MergeMEEG_HiLoRate,self).__init__()
        self.path     = None
        self.name     = None
        self.filename = None
        self.raw      = None
        self.system   = system
        self.startcode= 128
          
        self._verbose = False
        self._debug   = False
          
        self.data          = np.array([])
        self.times         = np.array([])
        self.ev_onsets     = np.array([])
        self.tsl_resamples = np.array([],dtype=np.int64)
        self.tsl_onset     = None
        self.time_delta    = None
        self.picks         = None
        self.is_data_size_adjusted = False
        
       #---meg defaults
        self.event_parameter = {'and_mask':255,'stim_type':'STIMULUS','response_shift':None}
        self.events          = {'consecutive': True, 'output': 'step', 'stim_channel': 'STI 014','min_duration': 0.00001, 'shortest_event': 1, 'mask': None}
                   
    @property   
    def and_mask(self):    return self.event_parameter['and_mask']
    @and_mask.setter
    def and_mask(self,v):  self.event_parameter['and_mask'] = v
      
    @property    
    def stim_type(self):   return self.event_parameter['stim_type']
    @stim_type.setter
    def stim_type(self,v): self.event_parameter['stim_type'] = v
      
    @property   
    def response_shift(self):  return self.event_parameter['response_shift']
    @response_shift.setter
    def response_shift(self,v):self.event_parameter['response_shift'] = v
  
    @property    
    def consecutive(self):   return self.events['consecutive']
    @consecutive.setter
    def consecutive(self,v): self.events['consecutive'] = v
    
    @property    
    def output(self):   return self.events['output']
    @output.setter
    def output(self,v): self.events['output'] = v
    
    @property    
    def stim_channel(self):   return self.events['stim_channel']
    @stim_channel.setter
    def stim_channel(self,v): self.events['stim_channel'] = str(v)
  
    @property  
    def min_duration(self):  return self.events['min_duration']
    @min_duration.setter
    def min_duration(self,v):self.events['min_duration'] = v
      
    @property
    def shortest_event(self):  return self.event_parameter['shortest_event']
    @shortest_event.setter
    def shortest_event(self,v):self.event_parameter['shortest_event'] = v
     
    @property      
    def verbose(self):   return self._verbose
    @verbose.setter
    def verbose(self,v): self._verbose=v
      
    @property    
    def debug(self): return self._debug
    @debug.setter
    def debug(self,v):
        self.verbose = v
        self._debug  = v

    @property
    def time_onset(self):    return self.raw.times[self.tsl_onset]
    @property
    def time_end(self):      return self.raw.times[-1]
    @property
    def time_duration(self): return self.raw.times[self.raw.last_samp - self.tsl_onset]
    @property
    def tsl_end(self):       return self.tsl_onset + self.times.shape[0]
    
    def reset(self):
        """ resets all data to None or np.array([]) """
        self.data          = np.array([])
        self.times         = np.array([])
        self.ev_onsets     = np.array([])
        self.tsl_resamples = np.array([],dtype=np.int64)
        self.tsl_onset     = None
        self.time_delta    = None
        self.picks         = None
        self.raw           = None
      
    def check_path(self):
        """ 
         Helper to check path for obj.filename
         assert error if no such file 
           
         Results
         -------
         True
        """
        print(" --> check path & file: " + self.system + " file name: " + str(self.filename))
        assert( os.path.isfile( self.filename ) ),"---> ERROR " + self.system +" file: no such file: " + str(self.filename)
        print("  -> OK")
        return True

    def init_times(self,time_duration=None):
        """
         init times as np-array
         
         Parameter
         ---------
         time_duration : <None> 
                         if not set use class time_duration
        """
        # MNE 0.15.2 mne.raw.time_as_index returns np.array 
        
        if time_duration:
           dtsl = np.int64( self.raw.time_as_index( time_duration )[0] )
        else:
           dtsl = np.int64( self.raw.time_as_index( self.time_duration )[0] )
      
        self.times = np.zeros(dtsl)
        dtsl      += self.tsl_onset
        if (dtsl > self.raw.last_samp):
           dtsl = None # include last idx
        self.times[:]= self.raw.times[self.tsl_onset:dtsl]
        self.times  -= self.times[0]  # start time _onsetseq at zero

    def time_info(self,channel_info=False):
        """
         prints info about time onset duration ... 
           
         Parameter
         ---------
          channel_info: if True prints info for channels in picks
        """
        jb.line()
        print(" --> " + self.system)
        print("  -> Time start: %12.3f end: %12.3f delta: %12.3f" % (self.time_onset,self.time_end,self.time_duration))
        print("  -> TSL  start: %12.3f end: %12.3f" % (self.tsl_onset,self.raw.last_samp))
        jb.line()          

        if ( channel_info ):
           print("  -> channel info: ")
           print("  ->  names      : " + ",".join([self.raw.ch_names[i] for i in self.picks]) )
           print("  ->  index      : " + str(self.picks))
           print(" -->  resamples  : %d" % (self.tsl_resamples.shape[0]))
           jb.line()

    def adjust_data_size(self):
        """
         adjust size in raw data with respect to tsl onset and end
        """
        self.raw._data = self.raw._data[:, self.tsl_onset:self.tsl_end]  #+1
        self.is_data_size_adjusted = True

    def get_onset_and_events(self):
        """
         find events with mne.find_events
         for <eeg brainvision  response data> add response shift to events
         find startcode in events
         
         Results:
         ---------
         index of startcode event onset 
         event onset array  without zeros
        """
        print(" --> call mne find events")
        ev_start_code_onset_idx = None
          
        ev = mne.find_events(self.raw, **self.events)
          
        if self.and_mask:
           ev[:, 1] = np.bitwise_and(ev[:, 1], self.and_mask)
           ev[:, 2] = np.bitwise_and(ev[:, 2], self.and_mask)
  
       #--- brainvision response_shift correction if response channel
        if ( ( self.system =='EEG') and ( self.stim_type == 'RESPONSE') ):
           ev[:, 1] -= self.response_shift  
           ev[:, 2] -= self.response_shift  
      
        ev_onsets  = np.squeeze( ev[np.where( ev[:,2] ),:])  # > 0

       #--- check  if no startcode  -> startcode not in/any  np.unique(ev[:, 2])
        if ( self.startcode in np.unique(ev[:, 2]) ):
           if ev_onsets.ndim > 1 :
              ev_id_idx = np.squeeze( np.where( np.in1d( ev_onsets[:,2],self.startcode )))
              ev_start_code_onset_idx =  np.int64( ev_onsets[ ev_id_idx,:] )[0].flatten()[0]
           else: # only one event code
              ev_start_code_onset_idx =  ev_onsets[ 0 ]
              ev_onsets = np.array([ev_onsets])
              ev_id_idx = 0 
        else:
           print("---> ERROR no startcode found %d " % (self.startcode))
           print("---> Events: ")
           print( np.unique(ev[:, 2]))
           print("\n")
           assert"ERROR no startcode found in events"              
          
        if self.verbose:
           jb.line()
           print(" --> Onset & Events Info : " + self.system )
           print("  -> Onset index         : {}".format( ev_start_code_onset_idx))
           if self.debug:
              print("  -> Onsets              :")
              print(ev_onsets)
           jb.line()
            
        return ev_start_code_onset_idx,ev_onsets 


class JuMEG_MergeMEEG(JuMEG_Base_IO):
    """
    Class JuMEG_MergeMEEG
     -> merge BrainVision ECG/EOG signals into MEG Fif file
     -> finding common onset via startcode in TRIGGER channel e.g <STI 014> <STI 013>
     -> filter data FIR lp butter 200Hz / 400Hz
     -> downsampling eeg data, srate sould be igher than meg e.g. eeg:5kHz meg:1017.25Hz
     -> rename groups and channel names dynamic & automatic !!!
     meg EEG 0001 -> ECG group ecg
     meg EEG 0002 -> EOG_xxx group eog
     meg EEG 0003 -> EOG_xxx group ecg

     Parameters:
     -----------     
      adjust= True : ajust raw-obj data size to startcode-onset and last common sample beween MEG and EEG data
      save  = True : save merged raw-obj

      parameter set via obj:

        meg_fname  = None <full file name>
        eeg_fname  = None <eeg brainvision vhdr full file name> with extention <.vhdr>  
        meeg_extention    = ",meeg-raw.fif" output extention

        stim_channel               = 'STI 014'
        startcode                  = 128  start code for common onset in <stim_channel>
             
        brainvision_channel_type   = 'STIMULUS'
        brainvision_stim_channel   = 'STI 014'
        brainvision_response_shift = 1000 used for mne.io.read_raw_brainvision will be added to the response value

        flags:
          verbose        = False
          do_adjust_size = True
          do_save        = True
          filter_meg     = False
          filter_eeg     = True

        filter option: can be canged via <obj.filter>
        filter.filter_method = "bw"
        filter.filter_type   ='lp'
        filter.fcut1         = None -> automatic selected  200Hz or 400Hz
              
              
     Results:
     --------
      raw obj; new meeg file name
    """
    def __init__(self,adjust_size=True,save=True,startcode=128,copy_eeg_events_to_trigger=False,filter_meg=False,filter_eeg=True,
                 meg={'stim_channel':'STI 014','min_duration':0.002,'shortest_event':3 },
                 eeg={'stim_channel':'STI 014','response_shift':1000,'stim_type':'STIMULUS','and_mask':None} ):
        
        # meg={'stim_channel':'STI 013'},eeg={'stim_channel':'STI 014','response_shift':1000,'stim_type':'RESPONSE','and_mask':None} 
        
        super(JuMEG_MergeMEEG,self).__init__()

        self.meg = JuMEG_MergeMEEG_HiLoRate(system='MEG')
        self.meg.stim_channel   = meg['stim_channel']
        self.meg.shortest_event = meg['shortest_event'] 
        self.meg.min_duration   = meg['min_duration'] 
              
        self.eeg = JuMEG_MergeMEEG_HiLoRate(system='EEG')
        self.eeg.stim_channel   = eeg["stim_channel"]
        self.eeg.response_shift = eeg["response_shift"] # brainvision_response_shift to mark response bits to higher 8bit in STI channel
        self.eeg.stim_type      = eeg["stim_type"]
        self.eeg.and_mask       = eeg['and_mask']
        #self.eeg.startcode      = startcode
        self.brainvision_response_shift = self.eeg.response_shift
        
        self.copy_eeg_events_to_trigger = copy_eeg_events_to_trigger
        
       #--- output
        self.meeg_fname     = None
        self.meeg_extention = ",meeg-raw.fif"

       #--- change channel names and group
       # self.channel_types = {'EEG 001': u'ecg', 'EEG 002': u'eog', 'EEG 003': u'eog'}
       # self.channel_names = {'EEG 001': u'ECG 001', 'EEG 002': u'EOG hor', 'EEG 003': u'EOG ver'}

      #--- filter obj
        self.filter     = jumeg_filter( filter_method="bw",filter_type='lp',fcut1=None,fcut2=None,remove_dcoffset=False,notch=[] )
        self.__event_id = 128
     
        self.verbose      = False
        self.debug        = False
        self.do_adjust_data_size = adjust_size
        self.do_save        = save
        self.do_filter_meg  = filter_meg
        self.do_filter_eeg  = filter_eeg
        #self.do_check_data_drift = check_data_drift

        self.startcode          = startcode
        self.__default_event_id = 128

        self.bads_list      = []
  
    @property  
    def default_start_code(self):  return self.__default_event_id

    @property
    def event_id(self):  return self.__event_id
    @event_id.setter
    def event_id(self, v):
        self.__event_id    = v 
        self.meg.startcode = v
        self.eeg.startcode = v
    
    @property    
    def startcode(self):   return self.event_id
    @startcode.setter
    def startcode(self,v): self.event_id = v
        
    def check_ids(self):
        """ 
        check data 
        Result
        ------
        True or assert Error
        """
        im= self.get_id(f=self.meg.filename)
        ie= self.get_id(f=self.eeg.filename)
        assert(set( im.split() ) == set( ie.split() ) ), "ERROR -> check IDs: MEG: " + str(im) +" EEG: " + str(ie)
        return True

    def check_filter_parameter(self):
        """  
         check filter parameter 
        
         Result
         ------
         low pass value
         
        """

        if self.meg.raw.info['sfreq'] > self.eeg.raw.info['sfreq']:
           assert "Warning EEG data sampling fequency %4.3f is lower than MEG data %4.3f " % (self.eeg.raw.info['sfreq'], self.meg.raw.info['sfreq'])
           # return False
        return self.filter.calc_lowpass_value( self.meg.raw.info['sfreq'] )

    def apply_filter_meg_eeg(self):
        """
         inplace filter all meg and eeg data except trigger channel with  lp
         using meg butter filter (FB)
        """
      #--- meg
        print("---> Start filter data")
        self.filter.fcut1 = self.check_filter_parameter()
        
        if self.do_filter_meg:    
           print(" --> Start filter data")
           self.filter.sampling_frequency = self.meg.raw.info['sfreq']
           print("  -> filter info: " + self.filter.filter_info)
           self.filter.apply_filter(self.meg.raw._data,picks=self.meg.picks)
           print("  -> Done filter meg")
      # ---  bv eeg
        if self.do_filter_eeg:
           print(" --> Start filter bv eeg data")
           self.filter.sampling_frequency = self.eeg.raw.info['sfreq']
           print("  -> filter info: " + self.filter.filter_info)
           self.filter.apply_filter(self.eeg.raw._data, picks=self.eeg.picks)
           print("  -> Done filter eeg")

    def get_resample_index(self,timepoints_high_srate=None,timepoints_low_srate=None,sfreq_high=None):
        """
         Downsampling function to resample signal of samp_length from
         higher sampling frequency to lower sampling frequency.

         Parameters
         ----------
         input:
           timepoints_low_srate : np.array of time points with lower  sampling rate less size than the other
           timepoints_high_self.meg.raw._data[self.meg.raw.ch_names.index(chname), self.meg.tsl_onset:self.meg.tsl_end] = srate: np.array of time points with higher sampling rate
           sfreq_high           : higher sampling frequency.

         Results
         --------
          resamp_idx: np.array of index of <timepoints_high_srate> to downsampled high sampled signal.
        """
        
        import numpy as np
       #---ToDo implementation in C for speed ???
        eps_limit  = round((0.90 / sfreq_high), 6) # distance  beween timepoints high/low  us
        resamp_idx = np.zeros( timepoints_low_srate.shape[0],dtype=np.int64 )
        j = 0
        idx=0
        for idx in np.arange(timepoints_low_srate.shape[0],dtype=np.int64):
            while (timepoints_low_srate[idx] - timepoints_high_srate[j] ) > eps_limit:
                   j += 1
            resamp_idx[idx] = j
            j += 1
        return resamp_idx

    def check_data_drift(self):
        """
         check data drift: if last common meg/eeg event code onset is in time resolution uncertainty
         dt < 1 x meg sampling periode
        
        Results
        ---------
        time differences from startcode onsets between meg and eeg as numpy array in samples
        """
                                             
        meg_samp_periode = 1000.0 / self.meg.raw.info['sfreq']
                        
        eeg_code_idx = np.where( ( self.eeg.ev_onsets[:,-1] < self.eeg.response_shift ) & ( self.eeg.ev_onsets[:,0] >= self.eeg.tsl_onset ) )[0]
        eeg_code     = self.eeg.ev_onsets[eeg_code_idx,-1].flatten()
        eeg_counts   = eeg_code.shape[0]
        
        meg_code_idx      = np.where( self.meg.ev_onsets[:,0] >= self.meg.tsl_onset )[0]
        meg_code          = self.meg.ev_onsets[meg_code_idx,-1].flatten()
        meg_counts        = meg_code.shape[0]
         
        meeg_counts = meg_counts
        if eeg_counts < meeg_counts:
           meeg_counts = eeg_counts  
        meeg_idx = meeg_counts -1    
        
        meg_dt_last_idx = self.meg.ev_onsets[ meg_code_idx[meeg_idx],0 ] - self.meg.tsl_onset
        meg_dt_last     = self.meg.raw.times[ meg_dt_last_idx ]
        eeg_dt_last_idx = self.eeg.ev_onsets[ eeg_code_idx[meeg_idx],0 ] - self.eeg.tsl_onset
        eeg_dt_last     = self.eeg.raw.times[ eeg_dt_last_idx ]
        dif_dt_last     = np.abs(meg_dt_last - eeg_dt_last)
        dmeeg    =  np.zeros(meg_counts)      
        
        if self.verbose:
           print("\n --> check data drift:")  
          
           if self.debug:
              jb.line()
              print("\n  -> MEG codes:")
              print(meg_code)
              print("\n  -> EEG codes [ exclude RESPONSE codes ]:")
              print(eeg_code)
              print("  -> Info MEG/EEG onsets:  code  t[s]")   
              jb.line()
              i=0
              dmeeg    =  np.zeros(meg_counts) 
            
              while i < meeg_counts:
                  megcode  = meg_code[i]
                  megonset = self.meg.raw.times[ self.meg.ev_onsets[meg_code_idx[i],0] - self.meg.tsl_onset]
                  eegcode  = eeg_code[i]
                  eegonset = self.eeg.raw.times[ self.eeg.ev_onsets[eeg_code_idx[i],0] - self.eeg.tsl_onset]
                  dmeeg[i] = megonset - eegonset
                  print("->% 5d MEG code:% 7.1f t:% 10.4f  EEG code:% 7.1f t:% 10.4f div: % 7.5f" % (i,megcode,megonset,eegcode,eegonset,dmeeg[i]))
                  i+=1
    
           dmeeg_abs= abs(dmeeg)
        
           jb.line() 
           print("     MEG event counts: %8d" % (meg_counts))
           print("     EEG event counts: %8d" % (eeg_counts))
           jb.line()
           print("  -> Last Common Event Code:")
           print("     MEG last event onset        [s] : %0.6f" % (meg_dt_last))
           print("     EEG last event onset        [s] : %0.6f" % (eeg_dt_last))
           print("     dt  last event              [ms]: %0.6f" % (dif_dt_last))
           jb.line() 
           print("     MEG onset tsl            : %8d"   % (self.meg.tsl_onset))
           print("     EEG onset tsl            : %8d"   % (self.eeg.tsl_onset))
           print("     startcode                : %6d"   % (self.startcode))
           print("     meg sampling periode [ms]: %0.6f" % (meg_samp_periode))
           jb.line()
           if self.debug:
              print("     Diverence  abs(MEEG)")
              print("      AVG [ms]: % 3.5f"%( dmeeg_abs.mean()))
              print("      STD [ms]: % 3.5f"%( dmeeg_abs.std() ))
              print("      MIN [ms]: % 3.5f"%( dmeeg_abs.min() ))
              print("      MAX [ms]: % 3.5f"%( dmeeg_abs.max() ))
              jb.line()

        if ( dif_dt_last > meg_samp_periode ):
           ws=("\n -->ERROR Data Drift ->last common meg/eeg event-code-onset is not in time resolution uncertainty\n -->MEG: %s\n -->EEG: %s") %( self.meg.filename,self.eeg.filename)
           print( ws + "\n\n")
             
        return dif_dt_last
  
    def fill_zeros_with_last(self,v):
        """ 
         fill_zeros_with_last -> solves EEG Marker sampling problem 
         only BV markers onset is recorded as one timepoint/tslsampled with 5kHz
         down sampling will may lose some onset markers
         solution: extend marker onset till the next maker value occures
         https://stackoverflow.com/questions/30488961/fill-zero-values-of-1d-numpy-array-with-last-non-zero-values   
         
         Parameter
         ---------
          tsl to extend length of marker onset
         
        """
        arr    = np.zeros(len(v)+1)
        arr[1:]= v
        prev   = np.arange(len(arr))
        prev[arr == 0] = 0
        prev = np.maximum.accumulate(prev)
        return arr[prev][1:]
        
    def run(self):
        """ 
        run merge meg and eeg data
        
        Parameters
        ----------
         start jumeg_merger_meeg.py with -h
        
        Returns
        ---------
         fname: fif-file name
         raw  : raw obj

        """
        self.meg.verbose = self.verbose
        self.eeg.verbose = self.verbose
        self.meg.debug   = self.debug
        self.eeg.debug   = self.debug
   
        print("\n---> Start JuMEG MEEG Merger")  
        jb.line()
             
        self.meg.check_path()
        self.eeg.check_path()
        self.check_ids()
      
       #--- load BV eeg
        jb.line()
        print(" --> load EEG BrainVision data: " + self.eeg.filename)
        self.eeg.reset()
        self.eeg.raw,_ = self.get_raw_obj(self.eeg.filename,raw=self.eeg.raw)
       #--- get start code onset
        self.eeg.tsl_onset,self.eeg.ev_onsets = self.eeg.get_onset_and_events()
       # --- get ECG & EOG picks
        self.eeg.picks = self.picks.eeg(self.eeg.raw)

       # --- load meg
        jb.line()
        print(" --> load MEG data:             " + self.meg.filename)
        self.meg.reset()
        self.meg.raw, _   = self.get_raw_obj(self.meg.filename,raw=self.meg.raw)
       # --- start code onset
        self.meg.tsl_onset,self.meg.ev_onsets = self.meg.get_onset_and_events()
       # --- get MEG & Ref picks
        self.meg.picks = self.picks.exclude_trigger(self.meg.raw)

       #--- adjust data length
       # meg longer or shorter than eeg
       
        if (self.eeg.time_duration < self.meg.time_duration):
            self.meg.init_times(time_duration=self.eeg.time_duration)
            self.eeg.init_times(time_duration=self.eeg.time_duration)
        else:
            self.meg.init_times(time_duration=self.meg.time_duration)
            self.eeg.init_times(time_duration=self.meg.time_duration)

      #--- cp index tp form bv to meg-cannels
        self.eeg.tsl_resamples  = self.get_resample_index(timepoints_high_srate=self.eeg.times,timepoints_low_srate=self.meg.times,sfreq_high=self.eeg.raw.info['sfreq'])
        self.eeg.tsl_resamples += self.eeg.tsl_onset # shift index-values in array to onset

        self.meg.time_info(channel_info=False)
        self.eeg.time_info(channel_info=True)
        self.check_data_drift()

      # --- filter meg / eeg data; no trigger
        self.apply_filter_meg_eeg()

       #--- downsampe & merge
        meg_ch_idx = 1

       #--- !!! PITFALL
       # eeg: ECG EOG_hor EOG_ver
       # fif  Old style for our 4D ['EOG 001','ECG 001','EOG 002'] or New ['EEG 001','EEG 001','EEG 002']
        meg_picks_eeg = jb.picks.picks2labels(self.meg.raw, jb.picks.eeg_ecg_eog(self.meg.raw))

        print("\n  -> MEG Picks        : {}".format(jb.picks.eeg_ecg_eog(self.meg.raw)))
        print("  -> MEG Labels       : {}".format( meg_picks_eeg))
        meg_picks_eeg.sort()  # inplace
        print("  -> MEG Labels sorted: {}".format( meg_picks_eeg))
        print("  -> EEG Labels       : {}\n".format( self.eeg.raw.ch_names))

        for eeg_ch in ( self.eeg.raw.ch_names ):
           #print("EEG ch: {} meg list: {}".format(eeg_ch,meg_picks_eeg))
            meg_chname = None
            if not eeg_ch.startswith('E'): continue

            eeg_idx = self.eeg.raw.ch_names.index(eeg_ch)

            if eeg_ch in meg_picks_eeg:
               meg_chname = eeg_ch
            else:
               meg_chname = "EEG %03d" %(meg_ch_idx)
               if meg_chname in meg_picks_eeg:
                  meg_ch_idx += 1
               else:
                  meg_chname = None
                  for ch_meg in meg_picks_eeg:
                      if ch_meg.startswith(eeg_ch.replace('_',' ').split(' ')[0]):
                         meg_chname = ch_meg
                         meg_picks_eeg.remove(ch_meg)
                         break
               if not meg_chname:
                  ch_type =  mne.io.pick.channel_type(self.eeg.raw.info, eeg_idx )
                  self.add_channel(self.meg.raw,ch_name=eeg_ch,ch_type=ch_type)
                  meg_chname = eeg_ch
                  #print("!!! ERROR in JuMEG_MergeMEEG.run: copy EEG channel: {} idx:{} not in MEG data channel list: {}".format(eeg_ch, eeg_idx, meg_chname),file=sys.stderr)
                  #continue
               print("  -> copy EEG channel: {} idx:{} to MEG channel: {}".format(eeg_ch, eeg_idx, meg_chname))

              #--- copy eeg downsapled data into raw
               print("meg_chname      : {}".format(meg_chname))
               print("meg_chname index: {} ".format(self.meg.raw.ch_names.index(meg_chname)))
               print("eeg_index       : {}".format(eeg_idx))

               self.meg.raw._data[self.meg.raw.ch_names.index(meg_chname), self.meg.tsl_onset:self.meg.tsl_end] = self.eeg.raw._data[eeg_idx, self.eeg.tsl_resamples]
              #--- rename groups and ch names
               self.meg.raw.set_channel_types( { meg_chname:eeg_ch.split('_')[0].lower() } ) # e.g. ecg eog
               self.meg.raw.rename_channels(   { meg_chname:eeg_ch.replace('_',' ')      } )

        if self.copy_eeg_events_to_trigger:
           print("\n --> Do copy EEG events to Trigger channel: " + self.eeg.stim_channel)
           eeg_idx = self.eeg.raw.ch_names.index( self.eeg.stim_channel ) 
           deeg    = self.eeg.raw._data[eeg_idx]
           deeg[:] = self.fill_zeros_with_last(deeg)
           
           d    = self.meg.raw._data[self.meg.raw.ch_names.index(self.meg.stim_channel),self.meg.tsl_onset:self.meg.tsl_end]
           d[:] = deeg[self.eeg.tsl_resamples] - self.eeg.response_shift
           d[ np.where( d < 0 ) ] = 0        
           
      # --- adjust data size to merged data block -> cut meg-data to meg-onset <-> meg-end tsls
        if self.do_adjust_data_size:
           self.meg.adjust_data_size()
           print("Eventcode adjusted: " + self.meg.stim_channel)
           print(self.meg.raw._data[self.meg.raw.ch_names.index(self.meg.stim_channel)])
      
      #--- upate bads 
        if self.bads_list:
           self.update_bad_channels(None,raw=self.meg.raw,bads=self.bads_list)
           
       #--- save meeg
        jb.line()
        self.meeg_fname = self.get_fif_name(raw=self.meg.raw,extention=self.meeg_extention,update_raw_fname=True)
        print("---> start saving MEEG data: "+ self.meeg_fname)
        if self.do_save:
           self.apply_save_mne_data(self.meg.raw,fname=self.meeg_fname,overwrite=True)
        else:
           print(" -->set Bads; bad-channels in meeg-raw file:")
           print( self.picks.bads(self.meg.raw))
           jb.line()
        
        print("---> DONE merge BrainVision EEG data to MEG")
        jb.line()
        print("\n\n")

        return self.meeg_fname,self.meg.raw


#=========================================================================================
#==== script part
#=========================================================================================  
        
def apply_jumeg_merge_meeg(opt):
   """
   apply jumeg_merge_meeg
    
   Parameter
   ---------                 
    opt: argparser option obj
     
   Result
   -------
 
   """

   fn_raw_list = []
   opt_dict    = {}      
   jb.verbose = opt.verbose
   
   JuMEEG = JuMEG_MergeMEEG()
  #--- flags         
   JuMEEG.verbose    = opt.verbose        
   JuMEEG.debug      = opt.debug   
   JuMEEG.filter_meg = opt.filter_meg
   JuMEEG.filter_eeg = opt.filter_eeg

  #--- check if defined not None 
   if jb.isNotEmptyString(opt.meg_stim_channel) : JuMEEG.meg.stim_channel = opt.meg_stim_channel
   if jb.isNotEmptyString(opt.eeg_stim_channel) : JuMEEG.eeg.stim_channel = opt.eeg_stim_channel
   if jb.isNotEmptyString(opt.eeg_stim_type)    : JuMEEG.eeg.stim_type    = opt.eeg_stim_type
  #---  
   if jb.isNotEmpty(opt.eeg_response_shift)     : JuMEEG.eeg.response_shift = int(opt.eeg_response_shift)
   if jb.isNotEmpty(opt.eeg_and_mask)           : JuMEEG.eeg.and_mask       = int(opt.eeg_and_mask)
  
  #--- check for single file pair or list
   if jb.isNotEmptyString(opt.list_filename):
      fn_raw_list,opt_dict = JuMEEG.get_filename_list_from_file(opt.list_path + "/" + opt.list_filename,start_path=opt.meg_stage)
  #--- check for meg and eeg filename  
   elif ( jb.isNotEmptyString(opt.meg_filename) and jb.isNotEmptyString(opt.eeg_filename) ):
        fn_raw_list.append(opt.meg_filename)
        opt_dict[opt.meg_filename] = {'bads': None, 'feeg': opt.eeg_filename}
     
   if not fn_raw_list:
      jb.print_error("!!! ERROR jumeg_merger_meeg: no meg and/or eeg file to process !!!",head="jumeg_merge_meeg")
      return         
   
  #--- loop preproc for each fif file
   for fif_file in (fn_raw_list) :
       feeg = None
       fmeg = fif_file
           
       if opt_dict[fif_file]['feeg']:
          feeg = str(opt_dict[fif_file]['feeg'])
          if opt.eeg_stage:
             if os.path.isfile(opt.eeg_stage + '/' + feeg):
                feeg= opt.eeg_stage + '/' + feeg
          if opt.meg_stage:
             if os.path.isfile(opt.meg_stage + '/' + fmeg):
                fmeg= opt.meg_stage + '/' + fmeg
      
       JuMEEG.meg.filename = fmeg    
       JuMEEG.eeg.filename = feeg
              
      #--- ck bags add global bds                          
       JuMEEG.bads_list = []
       if opt.set_bads:
          JuMEEG.bads_list = opt.bads_list.split(',')
      #--- ck add individual bads  
       if opt_dict[fif_file].get("bads"):
          JuMEEG.bads_list.append( opt_dict[fif_file]['bads'].split(',') )
      #--- individual startcode     
       if opt_dict[fif_file].get("startcode"):
          JuMEEG.startcode = int( opt_dict[fif_file]["startcode"] )
       elif jb.isNumber(opt.startcode):
           JuMEEG.startcode = int(opt.startcode)
       else:
           JuMEEG.startcode = JuMEEG.default_start_code
       JuMEEG.run()
     
        
def get_args(self):
        """ get args using argparse.ArgumentParser ArgumentParser
            e.g: argparse  https://docs.python.org/3/library/argparse.html
            
        Results:
        --------
        parser.parse_args(), parser
        
        """    
        info_global = """
                      JuMEG Merge BrainVision EEG data to MEG Data

                      ---> merge eeg data with meg fif file 
                      jumeg_merge_meeg -fmeg  <xyz.fif> -feeg <xyz.vdr> -r
         
                      ---> merge eeg data with meg fif file from text file 
                      jumeg_merge_meeg.py -seeg /data/meg_store1/exp/INTEXT/eeg/INTEXT01/ -smeg /data/meg_store1/exp/INTEXT/mne/ -plist /data/meg_store1/exp/INTEXT/doc/ -flist intext_merge_meeg.txt -sc 5 -b -v -r
          
                      """
        info_meg_stage="""
                       meg stage: start path for meg files from list
                       -> start path to fif file directory structure
                       e.g. /data/megstore1/exp/INTEXT/mne/
                       """
        info_eeg_stage="""
                       eeg stage: start path for eeg files from list
                       -> start path to eeg file directory structure
                       e.g. /data/megstore1/exp/INTEXT/eeg/INTEXT01/
                       """
        info_flist = """
                     path to text file with fif/eeg file list:
                     intext_merge_list.txt 
          
                     207006_INTEXT01_170629_0852_2_c,rfDC-raw.fif --feeg=207006_2.vhdr
                     """       
       
   # --- parser


        parser = argparse.ArgumentParser(info_global)
 
       # ---meg input files
        parser.add_argument("-fmeg",     "--meg_filename",help="meg fif file + relative path to stage", metavar="MEG_FILENAME")
        parser.add_argument("-fmeg_ext", "--meg_file_extention",help="meg fif file extention", default="FIF files (*.fif)|*.fif", metavar="MEG_FILEEXTENTION")
        parser.add_argument("-smeg","--meg_stage", help=info_meg_stage,metavar="MEG_STAGE",default="/home/fboers/MEGBoers/data/exp/MEG94T/mne")
       
       #---eeg input files  
        parser.add_argument("-feeg", "--eeg_filename",help="<eeg vhdr> file + relative path to stage",metavar="EEG_FILENAME")
        parser.add_argument("-feeg_ext", "--eeg_file_extention",help="eeg file extention: for brainvision use *.vhdr", default="EEG files (*.vhdr)|*.vhdr", metavar="EEG_FILEEXTENTION")
        parser.add_argument("-seeg","--eeg_stage", help=info_eeg_stage,metavar="EEG_STAGE",default="/home/fboers/MEGBoers/data/exp/MEG94T/eeg") #os.getcwd())
       
       #---textfile  
        parser.add_argument("-flist","--list_filename",help="text file with list of files to process in batch mode",metavar="LIST_FILENAME")
        parser.add_argument("-flist_ext", "--list_file_extention",help="list fif file extention", default="list file (*.txt)|*.txt", metavar="LIST_FILEEXTENTION")
        parser.add_argument("-plist","--list_path", help=info_flist,default=os.getcwd(),metavar="LIST_PATH")
        
       #-- bads
        parser.add_argument("-bads", "--bads_list", help="apply bad channels to mark as bad works only with <--set_bads> flag",default=("MEG 007,MEG 142,MEG 156,RFM 011") ) 
        
       #--- parameter
        parser.add_argument("-sc",   "--startcode",type=int,help="start code marker to sync meeg and eeg data",default=128)
        parser.add_argument("-megst","--meg_stim_channel",  help="meg stimulus marker channel",default='STI 014')
        parser.add_argument("-eegst","--eeg_stim_channel",  help="eeg stimulus marker chennel",default='STI 014')
        parser.add_argument("-eegrt","--eeg_stim_type",     help="eeg stim type",              default='STIMULUS')
        parser.add_argument("-eegrs","--eeg_response_shift",help="eeg respose shift",type=int, default=1000)
        parser.add_argument("-eegam","--eeg_and_mask",      help="eeg and mask",     type=int, default=None)
           
       # ---flags:
        parser.add_argument("-fieeg", "--filter_eeg",action="store_true", help="filter eeg data") 
        parser.add_argument("-fimeg", "--filter_meg",action="store_true", help="filter meg data") 
        
        parser.add_argument("-b", "--set_bads",     action="store_true", help="apply default bad channels to mark as bad") 
        parser.add_argument("-v", "--verbose",      action="store_true", help="verbose mode")
        parser.add_argument("-d", "--debug",        action="store_true", help="debug mode")
        parser.add_argument("-r", "--run",          action="store_true", help="!!! EXECUTE & RUN this program !!!")
        parser.add_argument("-s", "--save",         action="store_true", help="save  output fif file")
        parser.set_defaults(filter_eeg=True)
        parser.set_defaults(save=True)
        
        return parser.parse_args(), parser

#=========================================================================================
#==== MAIN
#=========================================================================================
def main(argv):
  
    opt, parser = get_args(argv)
    if len(argv) < 2:
        parser.print_help()
        sys.exit()
   
    if opt.verbose :
       print("\n---> ARGV parameter:")
       print(" --> fmeg        : " + str(opt.meg_filename))
       print(" --> feeg        : " + str(opt.eeg_filename))
       jb.line()
       print(" --> stage meg   : " + str(opt.meg_stage))
       print(" --> stage eeg   : " + str(opt.eeg_stage))
       jb.line()
       print(" --> path  list  : " + str(opt.list_path))
       print(" --> fname list  : " + str(opt.list_filename))
       jb.line()
       print(" --> start code         : " + str(opt.startcode))
       print(" --> meg_stim_channel   : " + str(opt.meg_stim_channel))
       print(" --> eeg_stim_channel   : " + str(opt.eeg_stim_channel))
       print(" --> eeg_stim_type      : " + str(opt.eeg_stim_type))
       print(" --> eeg_response_shift : " + str(opt.eeg_response_shift))
       print(" --> eeg_and_mask       : " + str(opt.eeg_and_mask)) 
       jb.line()
       print(" --> filter meg data    : " +str(opt.filter_meg)) 
       print(" --> filter eeg data    : " +str(opt.filter_eeg))
       jb.line()
       print(" --> bads list   : " + str(opt.bads_list))
       print(" --> set bads [uses channels from bads list] : " + str(opt.set_bads))
       jb.line()
       print(" --> verbose     : " + str(opt.verbose))
       print(" --> debug       : " + str(opt.debug))
       print(" --> run         : " + str(opt.run))
       jb.line()
       print("\n\n")  
       

    if opt.run:
       apply_jumeg_merge_meeg(opt)

if __name__ == "__main__":
   main(sys.argv)


'''
EXAMPLE file

#--- 207006
#207006/INTEXT01/170629_0852/2/207006_INTEXT01_170629_0852_2_c,rfDC-raw.fif --feeg=207006_INTEXT01_002.vhdr
#207006/INTEXT01/170629_0852/3/207006_INTEXT01_170629_0852_3_c,rfDC-raw.fif --feeg=207006_INTEXT01_003.vhdr
#207006/INTEXT01/170629_0852/4/207006_INTEXT01_170629_0852_4_c,rfDC-raw.fif --feeg=207006_INTEXT01_004.vhdr
#207006/INTEXT01/170629_0852/5/207006_INTEXT01_170629_0852_5_c,rfDC-raw.fif --feeg=207006_INTEXT01_005.vhdr
#207006/INTEXT01/170629_0852/6/207006_INTEXT01_170629_0852_6_c,rfDC-raw.fif --feeg=207006_INTEXT01_006.vhdr
#207006/INTEXT01/170629_0852/7/207006_INTEXT01_170629_0852_7_c,rfDC-raw.fif --feeg=207006_INTEXT01_007.vhdr
#--- resting state
207006/INTEXT01/170629_1027/1/207006_INTEXT01_170629_1027_1_c,rfDC-raw.fif --feeg=207006_INTEXT01_restclosed.vhdr --startcode=128 --bads=MEG 007,MEG 142
#207006/INTEXT01/170629_1027/2/207006_INTEXT01_170629_1027_2_c,rfDC-raw.fif --feeg=207006_INTEXT01_restopen.vhdr --startcode=128
#
#--- 208548
#208548/INTEXT01/170706_0915/3/208548_INTEXT01_170706_0915_3_c,rfDC-raw.fif --feeg=208548_INTEXT01_001.vhdr 
#208548/INTEXT01/170706_0915/4/208548_INTEXT01_170706_0915_4_c,rfDC-raw.fif --feeg=208548_INTEXT01_002.vhdr 
#208548/INTEXT01/170706_0915/5/208548_INTEXT01_170706_0915_5_c,rfDC-raw.fif --feeg=208548_INTEXT01_003.vhdr 
#208548/INTEXT01/170706_0915/6/208548_INTEXT01_170706_0915_6_c,rfDC-raw.fif --feeg=208548_INTEXT01_004.vhdr 
#208548/INTEXT01/170706_0915/7/208548_INTEXT01_170706_0915_7_c,rfDC-raw.fif --feeg=208548_INTEXT01_005.vhdr 
#208548/INTEXT01/170706_0915/7/208548_INTEXT01_170706_0915_8_c,rfDC-raw.fif --feeg=208548_INTEXT01_006.vhdr 
#--- resting state
#208548/INTEXT01/170706_1030/1/208548_INTEXT01_170706_1030_1_c,rfDC-raw.fif --feeg=208548_INTEXT01_restclosed.vhdr
#208548/INTEXT01/170706_1030/2/208548_INTEXT01_170706_1030_2_c,rfDC-raw.fif --feeg=208548_INTEXT01_restopen.vhdr
#

#---  example cmd calls
#jumeg_merge_meeg.py -seeg /data/meg_store1/exp/INTEXT/eeg/INTEXT01/ -smeg /data/meg_store1/exp/INTEXT/mne/ -plist /data_meg_store1/exp/INTEXT/doc/ -flist intext_merge_meeg.txt -sc 5 -b -v -r

#jumeg_merge_meeg.py -seeg ~/MEGBoers/data/exp/INTEXT/eeg/INTEXT01/ -smeg ~/MEGBoers/data/exp/INTEXT/mne/ -plist ~/MEGBoers/data/exp/INTEXT/doc/ -flist intext_merge_meeg.txt -sc 5 -b -v -r -d

'''
