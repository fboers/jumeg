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
experiment   = "MEG94T0T2"
type         = "preproc"
stage        = os.path.expandvars("$JUMEG_TEST_DATA/../MEG94T/")
report_path  = os.path.join(stage,"reports",experiment)
report_fname = experiment+"_"+type
mkpath( report_path )
report_hdf   = os.path.join(report_path,report_fname +".hdf5")
report_html  = os.path.join(report_path,report_fname +".html")

path_mne = os.path.join(stage,"mne")

#--- open as hdf to add data
#MNEReport = mne.open_report(report_hdf)

os.remove( report_html )

MNEReport = mne.Report(info_fname=None,title="JuMEG Preproc "+experimnet,image_format='png',raw_psd=False,verbose=verbose)

ids = []
flist= [
"./205720/MEG94T0T2/131016_1325/1/205720_MEG94T0T2_131016_1325_1_c,rfDC,meeg-raw.fif",
#./205720/MEG94T0T2/131016_1325/2/205720_MEG94T0T2_131016_1325_2_c,rfDC,meeg-raw.fif
#./205720/MEG94T0T2/131016_1326/1/205720_MEG94T0T2_131016_1326_1_c,rfDC,meeg-raw.fif
#./205720/MEG94T0T2/131016_1326/2/205720_MEG94T0T2_131016_1326_2_c,rfDC,meeg-raw.fif

"./206720/MEG94T0T2/130820_1334/1/206720_MEG94T0T2_130820_1334_1_c,rfDC,meeg-raw.fif"
#./206720/MEG94T0T2/130820_1334/1/206720_MEG94T0T2_130820_1334_2_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1335/1/206720_MEG94T0T2_130820_1335_1_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1335/2/206720_MEG94T0T2_130820_1335_2_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1336/1/206720_MEG94T0T2_130820_1336_1_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1336/2/206720_MEG94T0T2_130820_1336_2_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1455/1/206720_MEG94T0T2_130820_1455_1_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1455/2/206720_MEG94T0T2_130820_1455_2_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1456/1/206720_MEG94T0T2_130820_1456_1_c,rfDC,meeg-raw.fif
#./206720/MEG94T0T2/130820_1456/2/206720_MEG94T0T2_130820_1456_2_c,rfDC,meeg-raw.fif
]


#ids runs sectio nr, ica

report_ids = dict()

for f in flist:
    run_dir = os.path.dirname( os.path.join(path_mne,f ) )
    fname   = os.path.basename(f)
    id      = fname.split("_")[0]
    if not report_ids.get(id,None):
       reports_ids[id][report] = mne.Report(info_fname=None,title="JuMEG Preproc " + experiment +" "+id,image_format='png',raw_psd=False,
                                    verbose=verbose)
       reports_ids[id][fname]  = experiment+"_"+type +"_"+id
       
    section = fname.replace("-raw.fif","")

    #MNEReport.parse_folder(run_dir,pattern='*meeg-raw.fif',render_bem=False)
   #--- NR
    caption = "NR-"+fname
    comment = "noise reducer"
    section = "NoiseReducer"
    fimages = []
    
    fimg = os.path.join(run_dir,"plots",fname.replace("-raw.fif",",nr-raw.png"))
    
    if os.path.isfile(fimg):
       img  = Image.open(fimg)
       fimg = fimg.replace(".pdf",".png")
       img.save(fimg,"PNG")
       print(" ---> done saving img: "+ fimg)
    else:
       fimg = fimg.replace(".pdf",".png")
       
    fimages.append(fimg)
    
    # print(fimages)
    reports_ids[id][report].add_images_to_section(fimages, caption, section=section,comment=comment)
 
   #--- BADs
 
   #--- ICA
    caption= "ICA-"+fname
    comment="ica"
    section="ICA"
    fimages = []
   
    fimages.append(os.path.join(run_dir,fname.replace("-raw.fif",",nr,bcc,int,ar,overview-plot.png")))
    reports_ids[id][report].add_images_to_section(fimages,caption,section=section,replace=True,comments=comment)

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
    
    
    
  
    reports_ids[id][report].save( reports_ids[id][fname] )
    
    print(MNEReport)
    print(report_html)

    #MNEReport.add_htmls_to_section(report,captions, section='custom', replace=False)

#id      = "211890"
#fhtml   =  os.path.join(report_path,"211890_INTEXT01_preproc.html")
#import codecs

#file=codecs.open(fhtml,"r") #b")
#htmls=str( file.read() )


#caption = id
#MNEReport.add_htmls_to_section(htmls, id, section="TEST HTML", replace=False)

#MNEReport.save(report_html)