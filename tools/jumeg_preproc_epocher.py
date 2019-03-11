#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
JuMEG interface to export 4D/BTi data into fif format using mne-python
 call to: mne.io.read_raw_bti
 https://martinos.org/mne/stable/generated/mne.io.read_raw_bti.html#mne.io.read_raw_bti
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 08.01.2019
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,sys,argparse,re
#import numpy as np
#import logging
import mne

from jumeg.jumeg_base import jumeg_base as jb
from jumeg.epocher.jumeg_epocher import jumeg_epocher


__version__= "2019.02.11.001"


#=========================================================================================
#==== script part
#=========================================================================================

def apply_epocher(opt,raw=None):
    """
    apply jumeg epocher
    extract events and epochs from fif  data using template
    
    Parameter
    ---------
     opt
     
    Outputfile
    ----------
    <raw>, -raw.fif

    Returns
    -------
    return mne.io.Raw instance
    """
    fif_stage = os.path.expandvars(os.path.expanduser( opt.fif_stage) ) +"/"
   
   #--- Epocher events
    if opt.apply_events:
       print("-" * 50)
       print("---> EPOCHER Events")
       print("  -> FIF File: " + opt.fname)
       print("  -> Template: " + template_name + "\n")
    
       evt_param = {"condition_list":opt.condition_list,
                    "template_path" :opt.template_path,
                    "template_name" :opt.template_name,
                    "verbose":opt.verbose
                   }
    
       raw,fname = jumeg_epocher.apply_events(fname,raw=raw,**evt_param)
    
   # --- Epocher epochs
    if opt.apply_epocher:
       print("-" * 50)
       print("---> EPOCHER Epochs")
       print("  -> FIF File: " + fname)
       print("  -> Template: " + template_name + "\n")
       ep_param = {
                   "condition_list" : opt.condition_list,
                   "template_path"  : opt.template_path,
                   "template_name"  : opt.template_name,
                   "verbose"        : opt.verbose,
                   "event_extention": opt.event_extention,
                   "save_condition" :{ "events": opt.save_events,"epochs":opt.save_epochs,"evoked":opt.save_evoked},
                     # "weights"       :{"mode":"equal","method":"median","skip_first":null}
                     # "exclude_events":{"eog_events":{"tmin":-0.4,"tmax":0.6} } },
                     }
       return raw
    
    
def get_args(self):
    """
    get args using argparse.ArgumentParser ArgumentParser
    e.g: argparse  https://docs.python.org/3/library/argparse.html

    jumeg wrapper for <mne.io.read_raw_bti>
    https://martinos.org/mne/stable/generated/mne.io.read_raw_bti.html#mne.io.read_raw_bti
    
    Results:
    --------
    parser.parse_args(), parser
    """
    info_global = """
                  JuMEG Epocher
                  generate events, epochs and evoked from fif file
                  template driven
                  used python version: {}
                  """.format(sys.version.replace("\n"," "))
    h_fif_stage= """
                 fif stage: start path for fif file
                 -> start path to fif file directory structure
                 e.g. /data/meg1/exp/M100/mne/
                 """
    h_template_name ="""name of epocher template without extention: M100 from M100_jumeg_epocher_template.json"""
    h_template_stage="""stage for <jumeg epocher template> file, default defined as env: $JUMEG_PATH_TEMPLATE_EPOCHER"""
    h_condition_list="""list of conditions to process; defined in template file"""
    
    h_verbose = "bool, str, int, or None"
    #h_overwrite         ="overwrite existing fif files"
    
   #--- parser
    parser = argparse.ArgumentParser(info_global)

   #--- fif input
    parser.add_argument("-sfif","--fif_stage",help=h_fif_stage,metavar="FIF_STAGE",default="{$JUMEG_PATH_MNE_IMPORT}")
   #--- fif input file
    parser.add_argument("-fin","--fif_filename",help="fif file + relative path to stage",metavar="FIF_FILENAME")
    parser.add_argument("-fif_ext","--fif_file_extention",help="fif file extention",default="FIF files (*.fif)|*.fif",
                        metavar="FIF_FILEEXTENTION")
   #--- jumeg template epocher
    parser.add_argument("-template_name","--template_name",help=h_template_name, default="default",metavar="TEMPLATE_FILE")
    parser.add_argument("-temp_ext","--template_file_extention",help="template file extention",default="epocher template files (*_jumeg_epocher_template.json)|*_jumeg_epocher_template.json",
                        metavar="TEMPLATE_FILEEXTENTION")

    parser.add_argument("-stemplate","--template_stage",   help=h_template_stage,default="{$JUMEG_PATH_TEMPLATE_EPOCHER}",
                        metavar="TEMPLATE_STAGE")
   #--- condition list
    parser.add_argument("-condis","--condition_list",help=h_condition_list, default="")

  #--- flags
    # parser.add_argument("-overwrite","--overwrite",   action="store_true",help=h_overwrite)
    parser.add_argument("-all","--all_conditions",     action="store_true",help="apply for all conditions in template")
    
    parser.add_argument("-save_events","--save_events",action="store_true",help="save events")
    parser.add_argument("-save_epochs","--save_epochs",action="store_true",help="save epoch file")
    parser.add_argument("-save_evoked","--save_evoked",action="store_true",help="save evoked file")
    
    parser.add_argument("-v",     "--verbose",        action="store_true",help=h_verbose)
    parser.add_argument("-r",     "--run",            action="store_true",help="!!! EXECUTE & RUN this program !!!")
  
  #--- init flags
    parser.set_defaults(save_events=True,save_epochs=True,save_evoked=True)
    
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
       msg = ["---> jumeg preproc epocher      : {}".format(__version__),
              "---> python sys version         : {}".format(sys.version_info),
              "-" * 50," --> ARGV parameter:"]
       for k,v in sorted(vars(opt).items()):
           msg.append(" --> {0:<30}: {1}".format(k,v))
       msg.append("-"*50 +"\n")
       jb.Log.info(msg)
       
    if opt.run: apply_epocher(opt)
    
   
if __name__ == "__main__":
   main(sys.argv)
