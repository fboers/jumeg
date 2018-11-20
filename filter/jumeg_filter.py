#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys,argparse
import numpy as np

from jumeg.jumeg_base  import jumeg_base as jb
from jumeg.filter.jumeg_filter_bw  import JuMEG_Filter_Bw
from jumeg.filter.jumeg_filter_mne import JuMEG_Filter_MNE

__version__= '2018.08.24.001'


'''
----------------------------------------------------------------------
--- jumeg_filter          --------------------------------------------
---------------------------------------------------------------------- 
 autor      : Frank Boers 
 email      : f.boers@fz-juelich.de
 last update: 31.08.2016
---------------------------------------------------------------------- 
 Butterworth filter design from  KD,JD
 Oppenheim, Schafer, "Discrete-Time Signal Processing"
----------------------------------------------------------------------
 OBJ interface to MNE filter functions
----------------------------------------------------------------------
excluded:   
 Window Sinc Filter are taken from:
 The Scientist and Engineer's Guide to Digital Signal Processing
 By Steven W. Smith, Ph.D.
 Chapter 16: Window-Sinc Filter
 http://www.dspguide.com/ch16.htm
----------------------------------------------------------------------

 Dependency:
  numpy
  scipy
  mne
----------------------------------------------------------------------
 How to use the jumeg filter
---------------------------------------------------------------------- 

from jumeg.filter import jumeg_filter

#===> set some global values
ftype = "bp"
fcut1 =  1.0
fcut2 = 45.0
srate = 1017.25 # sampling rate in Hz

#---> make some notches
notch_start = 50
notch_end   = 200
notch       = np.arange(notch_start,notch_end+1,notch_start) 

#===> make an MNE FIR FFT filter, bp1-45 OOcall to the MNE filter class
fi_mne_bp = jumeg_filter(filter_method="mne",filter_type=ftype,fcut1=fcut1,fcut2=fcut2,remove_dcoffset=True,sampling_frequency=srate,notch=notch)

#---> or apply notches from 50 100 150 250 300 ... 450 
fi_mne_bp.calc_notches(50)

#---> or apply notches from 50 100 150
fi_mne_bp.calc_notches(50,150)

#---> apply filter works inpalce !!!
fi_mne_bp.apply_filter(raw._data,picks)


#===> make a butter bp1-45 Hz with dc offset correction and notches at 50,100,150,200 Hz
fi_bw_bp = jumeg_filter( filter_method="bw",filter_type=ftype,fcut1=fcut1,fcut2=fcut2,remove_dcoffset=True,sampling_frequency=srate,notch=notch)

#---> or apply notches from 50 100 150 250 300 ... 450 
fi_bw_bp.calc_notches(50)

#---> apply filter works inpalce !!!   
fi_bw_bp.apply_filter(raw._data,picks)


#=== make some filter objects
fi_bw_obj = []
for i in range(0,2):
  fi_bw_obj.append = jumeg_filter( filter_method="bw",filter_type=ftype,fcut1=fcut1,fcut2=fcut2,remove_dcoffset=True,sampling_frequency=srate,notch=notch)

#---> change the Obj filter parameter
#- obj1 => low-pass 35Hz
fi_bw_obj[0].fcut1      = 35.0
fi_bw_obj[0].filter_type='lp'

#- obj2 => high-pass 10Hz
fi_bw_obj[1].fcut1      = 10.0
fi_bw_obj[1].filter_type='hp'

#- obj3 => band-pass 10-30Hz
fi_bw_obj[2].fcut1      = 10.0
fi_bw_obj[2].fcut2      = 30.0
fi_bw_obj[3].filter_type='bp'

#--->apply the filter to your data , !!! works inplace !!!
for i in range(0,2):
    fi_bw_obj[i].apply_filter(data[i,:])

#--->finaly get the obj related filter name postfix e.g. to save the filterd data
fi_bw_obj[0].filter_name_postfix
filp35Hz
#----------------------------------------------------------------------

'''

def jumeg_filter(filter_method="bw",filter_type='bp',fcut1=1.0,fcut2=45.0,remove_dcoffset=True,sampling_frequency=1017.25,
                 filter_window='blackmann',notch=np.array([]),notch_width=1.0,order=4,njobs=4,verbose=False,
                 mne_filter_method='fft',mne_filter_length='10s',trans_bandwith=0.5):
    
    if filter_method.lower() == "bw"  :
       #from jumeg.filter.jumeg_filter_bw import JuMEG_Filter_Bw
       return JuMEG_Filter_Bw(filter_type=filter_type,fcut1=fcut1, fcut2=fcut2, remove_dcoffset=remove_dcoffset, sampling_frequency=sampling_frequency,notch=notch, notch_width=notch_width,order=order,verbose=verbose)   	  
    else : 
       #from jumeg.filter.jumeg_filter_mne import JuMEG_Filter_MNE
       return JuMEG_Filter_MNE(filter_type=filter_type,njobs=njobs,fcut1=fcut1,fcut2=fcut2,remove_dcoffset=True,sampling_frequency=sampling_frequency,verbose=verbose,
                               mne_filter_method=mne_filter_method,mne_filter_length=mne_filter_length,trans_bandwith=trans_bandwith,notch=notch,notch_width=notch_width)
    #elif filter_method.lower() == "ws"  :
    #   from jumeg.filter.jumeg_filter_ws import JuMEG_Filter_Ws
    #   return JuMEG_Filter_Ws(filter_type=filter_type,fcut1=fcut1, fcut2=fcut2, remove_dcoffset=remove_dcoffset, sampling_frequency=sampling_frequency, filter_window=filter_window)
    #   #, notch=notch, notch_width=notch_width)


#=========================================================================================
#==== script part
#=========================================================================================      
def apply_filter(opt):
    """
    apply jumeg filter with argparser options
    
    load fif file (mne) get raw-obj
    calc  FIR FFT filter [bp,hp,lp,notches] for raw-obj data
    save raw-obj to new file
    filter_method : mne => fft mne-filter
                    bw  => fft butterwoth
                    ws  => fft - windowed sinc
    
    Parameter
    ---------                 
     opt: argparser option obj
     
    Result
    -------
    raw-obj
    """
    raw  = None
    fout = None
    jb.verbose = opt.verbose
   #--- generate filter obj reset no defaults
    filter_obj = jumeg_filter(filter_method=opt.method,filter_type=opt.type,fcut1=None,fcut2=None,
                              remove_dcoffset=False,notch=np.array([]),notch_width=1.0,order=4)
    
   # !!! Py3 type(opt.fcut  ) return < cls str>
   
   #--- check and set opt parameter    
    if jb.isNotEmpty(opt.fcut1): filter_obj.fcut1 = float(opt.fcut1)
   #--- 
    if jb.isNotEmpty(opt.fcut2): filter_obj.fcut2 = float(opt.fcut2)
   #--- 
    if jb.isNotEmpty(opt.order): filter_obj.order = float(opt.order)
   #--- calc notch array e.g. 50,100,150 .. max    
    if opt.notch:
       filter_obj.calc_notches(opt.notch,opt.notch_max)
       if jb.isNotEmpty(opt.notch_width): filter_obj.notch_width = float(opt.notch_width)
   #--- 
    filter_obj.filter_window   = opt.window
    filter_obj.remove_dcoffset = opt.remove_dcoffset
    filter_obj.verbose         = opt.verbose
       
    if opt.method.lower() == "mne":
      filter_obj.mne_filter_method = opt.mne_method
      if jb.isNotEmpty(opt.mne_length)        : filter_obj.mne_filter_length = float(opt.mne_length)
      if jb.isNotEmpty(opt.mne_trans_bandwith): filter_obj.trans_bandwith    = float(opt.mne_trans_bandwith)

   #--- load fif and generate obj 
   #--- input file fullpath
    fin  = ""
    if (opt.fif_stage).strip(): fin = opt.fif_stage +"/"
    fin += opt.fif_filename
  #--- check if fin file exist  
    if not jb.isFile(fin,head="<jumeg_filter>"): return
   
    print(" --> jumeg filter load MEG data: " + fin)
    raw, _  = jb.get_raw_obj(fin,raw=raw) 
   #--- get MEG & Ref picks
    picks = jb.picks.exclude_trigger(raw)
    filter_obj.sampling_frequency = raw.info['sfreq']
    
   #--- apply filter
    print(" --> jumeg filter apply filter")
    filter_obj.apply_filter(raw._data, picks=picks)   
    print(" --> jumeg filter info: " + filter_obj.filter_info)
    
    filter_obj.update_info_filter_settings(raw) # raw.info lowpass and highpass
  
   #--- make output filename
    name_raw = fin.split('-')[0]
    fout = name_raw + "," + filter_obj.filter_name_postfix + opt.file_extention
    raw.info['filename'] = fout
    
    if opt.save:
       fout = jb.apply_save_mne_data(raw,fname=fout)

    return raw


def get_args(self):
        """ get args using argparse.ArgumentParser ArgumentParser
            e.g: argparse  https://docs.python.org/3/library/argparse.html
            
        Results:
        --------
        parser.parse_args(), parser
        
        """    
        info_global = """
                      JuMEG Filter
                      filter meg data
                      """  
                      
        info_fif_stage="""
                       fif stage: start path for fif files from list
                       -> start path to fif file directory structure
                       e.g. /data/megstore1/exp/INTEXT/mne/
                       """


        help_notch="""
                   apply notches [Hz]
                   notch    : notch single number or more 50,100 or None
                   notch_max: single number or None
                   if <notch_max> is set a notch array will be calculated
                      start and steps are the first item from <notch> up to <notch_max>
                   Example:
                      -n 50,60,90 -nmax 200  
                       notch array=[50,60,90,100,150,200]
                   """
       #--- parser
        parser = argparse.ArgumentParser(info_global)
 
       #--- meg input files
        parser.add_argument("-fin",     "--fif_filename",      help="fif file + relative path to stage",                    metavar="FIF_FILENAME")
        parser.add_argument("-fif_ext", "--fif_file_extention",help="fif file extention", default="FIF files (*.fif)|*.fif",metavar="FIF_FILEEXTENTION")
        parser.add_argument("-sfif",    "--fif_stage",         help=info_fif_stage,       default="/home/fboers/MEGBoers/data/exp/MEG94T/mne/",metavar="FIF_STAGE")  #os.getcwd()
        
       #--- parameter
        parser.add_argument("-m",    "--method",choices=["bw","mne"],            help="method to filter => bw:<jumeg butter> or mne: <mne-FFT FIR>",default="bw")
        parser.add_argument("-t",    "--type",  choices=["bp","lp","hp","notch"],help="type of filter: for lp,hp use <fcut1> only; for bp use <fcut1> and <fcut2>",default="bp")
        parser.add_argument("-w",    "--window",choices=["blackmann","hamming"], help="filter window function",default='blackmann')
       
        parser.add_argument("-fc1",  "--fcut1",         help="fcut1 [Hz]",default=None)
        parser.add_argument("-fc2",  "--fcut2",         help="fcut2 [Hz]",default=None)
        parser.add_argument("-n",    "--notch",         help='notch single number or list "50,100" [Hz]') 
        parser.add_argument("-nmax", "--notch_max",     help= help_notch)
        parser.add_argument("-nw",   "--notch_width",   help='notch width [Hz]', default=1.0) 
        parser.add_argument("-or",   "--order",         help='order', default=4) 
        parser.add_argument("-ext",  "--file_extention",help="output file extention",default="-raw.fif")
                     
        parser.add_argument("-mne_m" ,"--mne_method",        help='mne filter method', default='fft') 
        parser.add_argument("-mne_l" ,"--mne_length",        help='mne filter length', default='10s') 
        parser.add_argument("-mne_tb","--mne_trans_bandwith",help='mne trans bandwith',default='0.5') 
        
       # ---flags:
        parser.add_argument("-dc","--remove_dcoffset",action="store_true", help="remove dcoffset") 
        parser.add_argument("-v", "--verbose",        action="store_true", help="verbose") 
        parser.add_argument("-r", "--run",            action="store_true", help="!!! EXECUTE & RUN this program !!!")
        parser.add_argument("-s", "--save", action="store_true", help="save output fif file")

        parser.add_argument("-tt", "--test", action="store_true", help="save output fif file")

        parser.set_defaults(save=True)
       
        return parser.parse_args(), parser

#=========================================================================================
#==== MAIN
#=========================================================================================
def main(argv):
  
    opt, parser = get_args(argv)
    if len(argv) < 2:
       parser.print_help()
       sys.exit(-1)

    if opt.verbose :
       jb.line()
       print("---> jumeg filter version: {}".format(__version__))
       print("---> python sys version  : {}".format(sys.version_info))
       jb.line
       print("\n---> file input parameter:")
       print(" --> fin        : " + str(opt.fif_filename))
       print(" --> fext       : " + str(opt.fif_file_extention))
       print(" --> stage      : " + str(opt.fif_stage))
       print(" --> output file extention : " + str(opt.file_extention))
       jb.line()
       print("\n---> filter parameter:")
       print(" --> method     : " + str(opt.method))
       print(" --> type       : " + str(opt.type))
       print(" --> window     : " + str(opt.window))
       print(" --> fcut1      : " + str(opt.fcut1))
       print(" --> fcut2      : " + str(opt.fcut2))
       print(" --> notch      : " + str(opt.notch)) 
       print(" --> notch max  : " + str(opt.notch_max)) 
       print(" --> notch width: " + str(opt.notch_width)) 
       print(" --> order      : " + str(opt.order)) 
       jb.line()
       print("\n---> MNE filter method (only):")
       print(" --> MNE method : " + str(opt.mne_method))
       print(" --> MNE length : " + str(opt.mne_length))
       print(" --> MNE tansition bandwith: " + str(opt.mne_trans_bandwith))
       jb.line()    
       print(" --> verbose     : " + str(opt.verbose))
       print(" --> run         : " + str(opt.run))
       jb.line()
       print("\n\n")  
       
    if opt.run: apply_filter(opt)    

if __name__ == "__main__":
    main(sys.argv)


