#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 16.12.19
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------


import os,logging
from distutils.dir_util import mkpath

import mne
from mne.report import Report
from PIL import Image

from jumeg.base.jumeg_base         import jumeg_base as jb
from jumeg.base.jumeg_base_config  import JuMEG_CONFIG_YAML_BASE as jCFG
from jumeg.base                    import jumeg_logger

logger = logging.getLogger("jumeg")

__version__= "2019.12.16.001"

jumeg_logger.setup_script_logging(logger=logger)

'''
report.parse_folder(data_path=path, pattern=['*audvis_raw.fif', '*-eve.fif'])
report.save('report.html', overwrite=True, open_browser=False)

report.add_figs_to_section(fig, captions='Left Auditory', section='evoked')
report.save('report.html', overwrite=True)

read from disk as HDF5
report.save('report.h5', overwrite=True)
report_from_disk = mne.open_report('report.h5')
print(report_from_disk)
TOdo



with mne.open_report('report.h5') as report:
    report.add_figs_to_section(fig,
                               captions='Left Auditory',
                               section='evoked',
                               replace=True)
    report.save('report_final.html')
    
    

noise reducer plots
add bads
ica contour plots

ica overview, controll ECG, EOG plots

epocher results

ggf GFP
'''

#--- mk report HDF5
verbose=True
experiment   = "INTEXT"
type         = "preproc"
report_path  = os.path.expandvars("$JUMEG_TEST_DATA/reports")
report_fname = experiment+"_"+type
mkpath(report_path)
report_hdf   = os.path.join(report_path,report_fname +".hdf5")
report_html  = os.path.join(report_path,report_fname +".html")

#--- open as hdf to add data
#MNEReport = mne.open_report(report_hdf)

os.remove( report_html )

MNEReport = mne.Report(info_fname=None,title="JuMEG Preproc",image_format='png',raw_psd=False,verbose=verbose)

ids = ["211855,211890"]

flist=[
       "211855/INTEXT01/190329_1004/6/211855_INTEXT01_190329_1004_6_c,rfDC,meeg-raw.fif",
       "211890/INTEXT01/190403_0955/1/211890_INTEXT01_190403_0955_1_c,rfDC,meeg-raw.fif"
    
      ]

path_mne = os.path.expandvars("$JUMEG_TEST_DATA/mne")

_flist=[
        "210857/QUATERS01/191210_1325/1/210857_QUATERS01_191210_1325_1_c,rfDC,meeg-raw.fif",
        "210857/QUATERS01/191210_1325/2/210857_QUATERS01_191210_1325_2_c,rfDC,meeg-raw.fif",
        "210857/QUATERS01/191210_1325/3/210857_QUATERS01_191210_1325_3_c,rfDC,meeg-raw.fif",
        "210857/QUATERS01/191210_1325/4/210857_QUATERS01_191210_1325_4_c,rfDC,meeg-raw.fif",
        "210857/QUATERS01/191210_1437/1/210857_QUATERS01_191210_1437_1_c,rfDC,meeg-raw.fif",
        "210857/QUATERS01/191210_1437/2/210857_QUATERS01_191210_1437_2_c,rfDC,meeg-raw.fif"
      ]
# "210857/QUATERS01/191210_1325/1/210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr,bcc,int,fibp0.10-45.0,ar-raw.fif",

_path_mne = "/data/MEG/meg_store1/exp/QUATERS/mne"

#ids runs sectio nr, ica

for f in flist:
    
    
    run_dir = os.path.dirname( os.path.join(path_mne,f ) )
    fname   = os.path.basename(f)
    id= fname.split("_")[0]
    section= fname.replace("-raw.fif","")

    #MNEReport.parse_folder(run_dir,pattern='*meeg-raw.fif',render_bem=False)
    
    caption = "NR-"+fname
    comment = "noise reducer"
    section = "NoiseReducer"
    fimages = []
    
    fimg = os.path.join(run_dir,"plots",fname.replace("-raw.fif",",nr-raw.png"))
    
    if os.path.isfile(fimg):
       img  = Image.open(fimg)
       fimg = fimg.replace(".pdf",".png")
       img.save(fimg,"PNG")
       print(" ---> done saving: "+ fimg)
    else:
       fimg = fimg.replace(".pdf",".png")
       
    fimages.append(fimg)
    
    print(fimages)
    MNEReport.add_images_to_section(fimages, caption, section=section) #"noise reducer")
 
    caption= "ICA-"+fname
    comment="ica"
    section="ICA"
    fimages = []
   
    fimages.append(os.path.join(run_dir,fname.replace("-raw.fif",",nr,bcc,int,ar,overview-plot.png")))
    MNEReport.add_images_to_section(fimages,caption,section=section,replace=True,comments="ALL")  #"noise reducer")

    #id = f.split("/")

    #report = mne.Report(info_fname=None,subjects_dir=run_dir+"/..",subject=id,title="TEST "+id,image_format='png',raw_psd=False,verbose=verbose)
   
    #report.subject=id
    #report.subject_dir=run_dir
    
    logger.info("---> MNE report subject dir: {}".format(run_dir))
   
 #--- get bads
    # MNEReport.parse_folder(run_dir, pattern='*bcc-raw.fif',render_bem=False)
    # /211890/INTEXT01/190403_0955/1/plots/211890_INTEXT01_190403_0955_1_c,rfDC,meeg,nr-raw.png
    # report.add_figs_to_section(fig, captions='NoiseReducer', section="NR PSD")
    
    #MNEReport.add_images_to_section(fimages, captions, scale=None, section=section, comments=comments) #"noise reducer")
    
    
    
  
    
    print(MNEReport)
    print(report_html)

    #MNEReport.add_htmls_to_section(report,captions, section='custom', replace=False)

id      = "211890"
fhtml   =  os.path.join(report_path,"211890_INTEXT01_preproc.html")
fhtml="/home/fboers/MEGBoers/programs/JuMEG/jumeg-py/jumeg-py-git-fboers-2019-09-13/jumeg/jumeg/base/pipelines/test01.html"

import codecs

file=codecs.open(fhtml,"r") #b")
htmls=str( file.read() )


caption = id

MNEReport.add_htmls_to_section(htmls, id, section="TEST HTML", replace=False)

MNEReport.save(report_html)