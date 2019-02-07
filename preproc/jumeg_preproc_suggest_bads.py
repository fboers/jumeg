#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
interface to jumeg_noise_reducer

"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 22.11.18
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------
import os,sys
import numpy as np
import logging

from jumeg.jumeg_base         import jumeg_base as jb
from jumeg.jumeg_suggest_bads import suggest_bads

__version__= "2018.12.04.001"


#=========================================================================================
#==== script part
#=========================================================================================

def apply_suggest_bads(opt):
    """
    apply jumeg noise reducer with argparser options

    load fif file (mne) get raw-obj
    apply noise reducer
    save raw-obj to new file
    plot or save PSD

    Parameter
    ---------
     like jumeg_noise_reducer

     fname_raw, raw=None, signals=[], noiseref=[], detrending=None,
     tmin=None, tmax=None, reflp=None, refhp=None, refnotch=None,
     exclude_artifacts=True, checkresults=True, return_raw=False,
     complementary_signal=False, fnout=None, verbose=False

    Outputfile
    ----------
    <wawa>,nr-raw.fif for input <wawa>-raw.fif

    Returns
    -------
    If return_raw is True, then mne.io.Raw instance is returned.

    """
   # --- check and set opt parameter

    tmin,tmax,reflp,refhp,refnotch = None,None,None,None,None

    if jb.isNotEmpty(opt.tmin): tmin = float(opt.tmin)
    if jb.isNotEmpty(opt.tmax): tmax = float(opt.tmax)
    if jb.isNotEmpty(opt.relp): relp = float(opt.relp)
    if jb.isNotEmpty(opt.rehp): rehp = float(opt.rehp)
    if jb.isNotEmpty(opt.refnotch): refnotch = float(opt.refnotch)

    signals=[]
    if jb.isNotEmpty(opt.signals): signals=opt.signals.split(',')
    noiseref=[]
    if jb.isNotEmpty(opt.noiseref): noiseref=opt.noiseref.split(',')

    refnotch=[]
    if jb.isNotEmpty(opt.refnotch): refnotch=np.fromstring(opt.refnotch)


   # --- ck file fullpath
    fin = ""
    if (opt.fif_stage).strip(): fin = opt.fif_stage + "/"
    fin += opt.fif_filename
   # --- check if fin file exist
    if not jb.isFile(fin, head="<jumeg_filter>"): return
   #--- run
    if opt.run:
       noise_reducer(fin,signals=signals, noiseref=noiseref, detrending=opt.detrending,
                     tmin=tmin, tmax=tmax, reflp=relp, refhp=rehp, refnotch=refnotch,
                     exclude_artifacts=opt.exclude_artifacts, checkresults=opt.checkresults,
                     complementary_signal=opt.complementary_signal,verbose=opt.verbose,fnout=None, return_raw=False)


def get_args(self):
    """
    get args using argparse.ArgumentParser ArgumentParser
    e.g: argparse  https://docs.python.org/3/library/argparse.html

    Results:
    --------
    parser.parse_args(), parser
    """

    def suggest_bads(raw,sensitivity_steps=97,sensitivity_psd=95,
                     fraction=0.001,epoch_length=None,summary_plot=False,
                     show_raw=False,validation=True):
        '''
        Function to suggest bad channels. The bad channels are identified using
        time domain methods looking for sharp jumps in short windows of data and
        in the frequency domain looking for channels with unusual power
        spectral densities.

        Note: This function is still in the development stage and contains a lot of
        hard coded values.

        Parameters
        ----------
        raw: str | mne.io.Raw
            Filename or the raw object.
        epoch_length: int | None
            Length of the window to apply methods on.
        summary_plot: bool
            Set True to generate a summary plot showing suggested bads.

        # parameters for step detection (AFP)
        # in %, 0 marks all chanels 100 marks none; percentile of

        # parameter for frequency analysis
        # in %, 0 marks all chanels 100 marks none; percentile of

        Returns
        -------
        suggest_bads: list
            List of suggested bad channels.
        raw: mne.io.Raw
            Raw object updated with suggested bad channels.
        '''
    
    
    
    
    
    
    
    info_global = """
                  JuMEG Noise Reducer
                  meg data noise reduction
                  used python version:
                   {}
                  """.format(sys.version.replace("\n"," "))
                 
    info_fif_stage="""
                   fif stage: start path for fif files from list
                   -> start path to fif file directory structure
                   e.g. /data/megstore1/exp/INTEXT/mne/
                   """
    h_signals="""
              List of channels to compensate using noiseref.
              If empty use the meg signal channels.
              signals may contain regexp, which are resolved
              using mne.pick_channels_regexp(). All other channels are copied.
              """
    h_noiseref ="""
                List of channels to use as noise reference.
                If empty use the magnetic reference channsls (default).
                noiseref may contain regexp, which are resolved
                using mne.pick_channels_regexp(). All other channels are copied.
                """
    h_tmin ="""
            lower latency bound for weight-calc [start of trace]
            Weights are calc'd for (tmin,tmax), but applied to entire data set
            """
    h_tmax ="""
            upper latency bound for weight-calc [ end  of trace]
            Weights are calc'd for (tmin,tmax), but applied to entire data set
            """
    h_refhp="""
            high-pass frequency for reference signal filter [None]
            
            reflp < refhp: band-stop filter
            reflp > refhp: band-pass filter
            reflp is not None, refhp is None: low-pass filter
            reflp is None, refhp is not None: high-pass filter 
            """
    h_reflp="""
            low-pass frequency for reference signal filter [None]
            reflp < refhp: band-stop filter
            reflp > refhp: band-pass filter
            reflp is not None, refhp is None: low-pass filter
            reflp is None, refhp is not None: high-pass filter
            """
    h_refnotch ="""
               (list of) notch frequencies for reference signal filter [None]
               use raw(ref)-notched(ref) as reference signal
               """
    h_exclude_artifacts="""
                        filter signal-channels thru _is_good() [True]
                        (parameters are at present hard-coded!)
                        """
    h_complementary_signal="""
                           replaced signal by traces that would be
                           subtracted [False]
                           (can be useful for debugging)
                           """
    h_detrending="""ctrl subtraction of linear trend from all magn. chans [False]"""
    h_checkresults="""control internal checks and overall success [True]"""

   #--- parser
    parser = argparse.ArgumentParser(info_global)

   #--- meg input files
    parser.add_argument("-fin",     "--fif_filename",      help="fif file + relative path to stage",                    metavar="FIF_FILENAME")
    parser.add_argument("-fif_ext", "--fif_file_extention",help="fif file extention", default="FIF files (*.fif)|*.fif",metavar="FIF_FILEEXTENTION")
    parser.add_argument("-sfif",    "--fif_stage",         help=info_fif_stage,       default="/home/fboers/MEGBoers/data/exp/MEG94T/mne/",metavar="FIF_STAGE")  #os.getcwd()

   #--- parameter
    parser.add_argument("-sig", "--signals",     help=h_signals, default=None)
    parser.add_argument("-tmin", "--tmin",       help=h_tmin,    default=None)
    parser.add_argument("-tmax", "--tmax",       help=h_tmax,    default=None)
    parser.add_argument("-relp", "--relp",       help=h_reflp,   default=None)
    parser.add_argument("-rehp", "--rehp",       help=h_refhp,   default=None)
    parser.add_argument("-noiseref","--noiseref",help=h_noiseref,default=None)
    parser.add_argument("-refnotch","--refnotch",help=h_refnotch,default=None)

   #---flags:
    parser.add_argument("-exclude_artifacts",   "--exclude_artifacts",   action="store_true", help=h_exclude_artifacts,default=True)
    parser.add_argument("-checkresults",        "--checkresults",        action="store_true", help=h_checkresults,default=True)
    parser.add_argument("-complementary_signal","--complementary_signal",action="store_true", help=h_complementary_signal)
    parser.add_argument("-detending",           "--detrending",          action="store_true", help=h_detrending)

    parser.add_argument("-v", "--verbose",                          action="store_true", help="verbose")
    parser.add_argument("-r", "--run",                              action="store_true", help="!!! EXECUTE & RUN this program !!!")

    return parser.parse_args(), parser

#=========================================================================================
#==== MAIN
#=========================================================================================
def main(argv):

    opt, parser = get_args(argv)
    if len(argv) < 2:
       parser.print_help()
       sys.exit(-1)

    line="-"*50

    if opt.verbose :
       jb.line()
       info=["---> jumeg preproc noise reducer version: {}".format(__version__),
             "---> python sys version  : {}".format(sys.version_info),
             line,
             "---> file input parameter:",
             " --> fin        : " + str(opt.fif_filename),
             " --> fext       : " + str(opt.fif_file_extention),
             " --> stage      : " + str(opt.fif_stage),
             " --> output file extention : " + str(opt.file_extention),
             line,
             "---> noise reducer parameter:",
             ]
       for k in ["signals","tmin","tmax","relp","rehp","noiseref","refnotch"]:
           info.append(" --> {}     : {}".format(k,opt.get(k,"not defined")))

       info.append(line)
       info.append("\n---> noise reducer flags:")
       for k in ["exclude_artifacts","checkresults", "complementary_signal", "detrending", "verbose", "run"]:
           info.append(" --> {}     : {}".format(k, opt.get(k,"not defined")))
       info.append(line)
       jb.Hlog.info( "\n".join(info)+"\n")
    if opt.run: apply_noise_reducer(opt)

if __name__ == "__main__":
   main(sys.argv)
