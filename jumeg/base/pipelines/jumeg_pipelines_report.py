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

class JuMEG_REPORT(object):
    def __init__(self,**kwargs):
        self.experiment = "TEST"
        self._stage      = "."
        
        self.config     = None
        self._fname      = None
        self.subject_id = "0815"
        self.verbose    = False
        self.debug      = False
       
        self.report_postfix   = "report"
        self.report_extention = ".html"
        self.image_extention  = ".png"
        self.image_format     = "png"
        
        self.write_hdf5       = True
        
        self._MNE_REPORT = None
        
        self._isOpen = False

    @property
    def stage(self): return self._stage
    @stage.setter
    def stage(self,v):
        self._stage = jb.expandvars(v)

    @property
    def fname(self):
        return self._fname

    @fname.setter
    def fname(self,v):
        self._fname = jb.expandvars(v)

    @property
    def Report(self):
        return self._MNE_REPORT
    @property
    def isOpen(self): return self._isOpen
    
    @property
    def report_path(self):
        return os.path.join(self.stage,self.report_postfix)

    @property
    def report_name(self):
        return self.experiment +"_"+ self.subject_id +"_"+ self.report_postfix + self.report_extention
    @property
    def report_fullname(self):
        return os.path.join(self.report_path,self.report_name)
    @property
    def title(self):
        return "JuMEG Preproc-"+self.experiment +"-"+ self.subject_id

    def _update_from_kwargs(self,**kwargs):
       
        self.fname            = kwargs.get("fname",self.fname)
        self.subject_id       = str(kwargs.get("subject_id",self.subject_id))
        self.experiment       = kwargs.get("experiment",self.experiment)
        self.report_postfix   = kwargs.get("report_postfix",self.report_postfix)
        self.report_extention = kwargs.get("report_extention",self.report_extention)
      #---
        self.config  = kwargs.get("config", self.config)
        self.verbose = kwargs.get("verbose",self.verbose)
        self.debug   = kwargs.get("debug",  self.debug)
       
        if kwargs.get("stage",None):
           stg = kwargs.get("stage",self.stage)
           if os.path.isdir(stg):
              self.stage = stg
        cfg = self.config.GetDataDict("report")
        self.write_hdf5 = cfg.get("hdf5",self.write_hdf5)
        
    def _open(self,**kwargs):
        """
        
        :param kwargs:
        :return:
        """
        '''
        ToDo open HDF5
        report_from_disk = mne.open_report('report.h5')
        with mne.open_report('report.h5') as report:
        report.add_figs_to_section(fig,
                               captions='Left Auditory',
                               section='evoked',
                               replace=True)
        report.save('report_final.html')

        '''
        
        
        self._isOpen = False
        try:
            if self.config.report.overwrite:
               os.remove(self.report_fullname)
        except:
            pass
        
        self._MNE_REPORT = mne.Report(info_fname=None,title=self.title,image_format= self.image_format,raw_psd=False,verbose=self.verbose)
        self._isOpen = True
        return self._isOpen
     
    def _check_image_extention(self,fimg):
        if os.path.isfile(fimg):
           if fimg.endswith("pdf"):
              #img  = Image.open(fimg)
              #fimg = fimg.replace(".pdf",self.image_extention)
              #img.save(fimg,self.image_format.upper())
              return False
           return fimg
        else:
           return False
    
    def _report_noise_reducer(self,config=None):
        """
        find img im plotdir
        convert to png
        add to report
        :param config:
        :return:
        """
        if not config: return False
        p        = os.path.dirname(self.fname)
        plot_dir = os.path.join(p,config.get("plot_dir"))
        
        img_files=[]
        captions=[]
        for file in os.listdir(plot_dir):
            fimg = self._check_image_extention( os.path.join(plot_dir,file) )
            if not fimg : continue
            if file.endswith( config.get("postfix","nr") +"-raw"+self.image_extention ):
               img_files.append(fimg)
               captions.append("NR-" + os.path.basename( fimg.rsplit(self.image_extention,1)[0] ) )
               
        self.Report.add_images_to_section(img_files,captions=captions,section="Noise Reducer",replace=True)  #,comments=comments)
        
        logger.info("---> report noise reducer files found: {}".format(img_files))
       
        return True

    def _report_ica(self,config=None):
        
        ToDo sort chops
        filtered non fitered
        use slider for each  as fig
        
        if not config: return False
        p = os.path.dirname(self.fname)
        plot_dir = os.path.join(p,"ica/plots") #config.get("plot_dir"))
      
        img_files = []
        captions = []
        
        ext = "-"+config.get("postfix","ar") + self.image_extention
        
        for file in os.listdir(plot_dir):
            fimg = self._check_image_extention(os.path.join(plot_dir,file))
            if not fimg: continue
            if file.endswith(ext):
               img_files.append(fimg)
        img_files.sort()
        img_files.reverse()
        for fimg in img_files:
            captions.append( "AR-"+os.path.basename(fimg.replace(ext,"")))
    
        self.Report.add_images_to_section(img_files,captions=captions,section="ICA",
                                          replace=True)  #,comments=comments)
    
        logger.info("---> report ica files found:\n {}".format(img_files))
    
      
    
    
    def save(self,fname=None):
        if self.isOpen:
           if not fname:
              fname = self.report_fullname
           
           mkpath(self.report_path)
           
           cfg = self.config.GetDataDict("report")
         #--- html
           self.Report.save(fname, overwrite=cfg.get("overwrite"),open_browser=True)
         #--- h5
           if self.write_hdf5:
              self.Report.save(fname.replace(self.report_extention,".h5"), overwrite=cfg.get("overwrite"), open_browser=False)

           logger.info("---> DONE saving JuMEG report: HDF5: {}\n  -> file {}".format(self.write_hdf5,fname))
        else:
           logger.exception("---> ERROR in saving JuMEG report: {}\n ---> Report not open\n".format(fname))
        return self.isOpen

    def run(self,**kwargs):
        self._update_from_kwargs(**kwargs)
        
        if not self._open(): return False
      #--- noise reducer
        cfg = self.config.GetDataDict("report")
        
        if cfg.get("noise_reducer",False):
            self._report_noise_reducer(config=self.config.GetDataDict("noise_reducer"))
    
      #--- ica
        if cfg.get("ica",False):
           self._report_ica(config=self.config.GetDataDict("ica"))
   
        if cfg.get("save",False):
           self.save()


def test1():
    #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger)

    stage = "$JUMEG_PATH_LOCAL_DATA/exp/QUATERS/mne"
    fcfg  = os.path.join("/home/fboers/MEGBoers/programs/JuMEG/jumeg-py/jumeg-py-git-fboers/jumeg/pipelines","jumeg_config.yaml")
    
    fpath = "210857/QUATERS01/191210_1325/1"
    path  = os.path.join(stage,fpath)
    raw_fname = "210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr,bcc,int-raw.fif"
    fname     = os.path.join(path,raw_fname)
    
   #--- read config
    from jumeg.base.jumeg_base_config import JuMEG_CONFIG_YAML_BASE as jCFG
    CFG = jCFG()
    CFG.update(config=fcfg)
    #config = CFG.GetDataDict("ica")
    
    #CFG.info()
    
    jReport = JuMEG_REPORT()
    jReport.run(stage=stage,fname=fname,subject_id=210857,config=CFG)
    
    
if __name__ == "__main__":
    test1()
    
'''
    def __report(self):
    
        figs = []
        flist = []
        captions = []
        sctions = []
        comments = []
        fraw = os.path.basename(jb.get_raw_filename(self.raw))
    
        self.Plot.n_plots = 2
        self.Plot.save = False
        self.Plot.verbose = True
        self.Plot.fout = fraw.rsplit("-",1)[0]
        self.Plot.fout += "-ar"
    
        channels = [["ECG",999],["EOG ver",997],["EOG hor",998]]
    
        self.Plot.n_rows = 2
        self.Plot.n_cols = 3  # len(channels) / 2
        self.Plot.idx = 1
        idx = 1
    
        for ch in channels:
            idx += 1
            #self.Plot.fout= fout+ ch[0]+".png"
            #self.Plot.fout.replace(" ","_")
            print(ch[0])
            print(ch[1])
            self.plot(ch_name=ch[0],event_id=ch[1],picks=self.picks,tmin=-0.4,tmax=0.4,show=False)
            self.Plot.idx = idx
    
        #self.Plot.figure.show()
        self.Plot.save_figure()
        flist.append(self.Plot.fout)
        figs.append(self.Plot.figure)
        captions.append(self.Plot.fout)
        comments.append(ch[0])
        #sections.append(ch[0])
    
        report_html = 'test02.html'
        verbose = True
    
        try:
            os.remove(report_html)
        except:
            pass
    
        #sections = captions #fraw
        #captions = [fraw,fraw,fraw]
    
        report = mne.Report(info_fname=None,title="JuMEG Preproc",image_format='png',raw_psd=False,verbose=verbose)
        report.add_images_to_section(flist,captions=captions,section="ICA",replace=True)  #,comments=comments)
    
        # report.add_figs_to_section(figs, captions=captions, section="ICA",replace=True)
    
        #report.add_slider_to_section(figs, captions=captions, section='ICA', title='Slider',replace=True)
    
        #report.add_slider_to_section(figs,captions=captions,section="ICA",title=fraw,replace=True)
    
        report.save(report_html)
    
        '''
'''
        fimg = os.path.join(run_dir,"plots",fname.replace("-raw.fif",",nr-raw.png"))

        if os.path.isfile(fimg):
            img = Image.open(fimg)
            fimg = fimg.replace(".pdf",".png")
            img.save(fimg,"PNG")
            print(" ---> done saving img: " + fimg)
        else:
            fimg = fimg.replace(".pdf",".png")

        fimages.append(fimg)
        '''
'''
        while figs:
            plt.close(fig=figs.pop())
        self.Plot.clear()


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



report.parse_folder(data_path=path,pattern=['*audvis_raw.fif','*-eve.fif'])
report.save('report.html',overwrite=True,open_browser=False)

report.add_figs_to_section(fig,captions='Left Auditory',section='evoked')
report.save('report.html',overwrite=True)

read
from disk as HDF5

report.save('report.h5',overwrite=True)

print(report_from_disk)
TOdo


'''

'''
#--- reports
reports:
    run: True
    save: True
    overwrite: False

    noise_reducer:
      run: True
    ica:
      run: True


def init_mne_report(raw_fname=None,raw=None,config=None):
    """
    """

    verbose = True


experiment = "MEG94T0T2"
type = "preproc"
stage = os.path.expandvars("$JUMEG_TEST_DATA/../MEG94T/")
report_path = os.path.join(stage,"reports",experiment)
report_fname = experiment + "_" + type
mkpath(report_path)
report_hdf = os.path.join(report_path,report_fname + ".hdf5")
report_html = os.path.join(report_path,report_fname + ".html")

path_mne = os.path.join(stage,"mne")


#--- open as hdf to add data
#MNEReport = mne.open_report(report_hdf)
'''