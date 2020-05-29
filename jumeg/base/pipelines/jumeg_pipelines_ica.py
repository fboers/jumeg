#!/usr/bin/env python3
# -+-coding: utf-8 -+-

#--------------------------------------------
# Authors:
# Frank Boers      <f.boers@fz-juelich.de>
# Christian Kiefer <c.kiefer@fz-juelich.de>
#--------------------------------------------
# Date: 12.112.19
#--------------------------------------------
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

import os,os.path as op
import numpy as np
import time,datetime

from distutils.dir_util import mkpath

import mne

from mne.preprocessing                    import ICA
#---
from jumeg.base                           import jumeg_logger
from jumeg.base.jumeg_base                import jumeg_base as jb
from jumeg.base.jumeg_base_config         import JuMEG_CONFIG as jCFG
#---
from jumeg.base.pipelines.jumeg_pipelines_ica_perfromance  import JuMEG_ICA_PERFORMANCE
from jumeg.base.pipelines.jumeg_pipelines_ica_svm          import JuMEG_ICA_SVM
from jumeg.base.pipelines.jumeg_pipelines_ica_utils        import fit_ica,ica_artefact_rejection_and_apply
#---
from jumeg.base.pipelines.jumeg_pipelines_chopper          import JuMEG_PIPELINES_CHOPPER

#---
from jumeg.filter.jumeg_mne_filter import JuMEG_MNE_FILTER

logger = jumeg_logger.get_logger()

__version__= "2020.05.28.001"

class JuMEG_PIPELINES_ICA(object):
    def __init__(self,**kwargs):
        super().__init__()
        
        self.PreFilter      = JuMEG_MNE_FILTER()
        self.Chopper        = JuMEG_PIPELINES_CHOPPER()
        self.ICAPerformance = JuMEG_ICA_PERFORMANCE()
        self.SVM            = JuMEG_ICA_SVM()
        
        self.useSVM         = False
        self.verbose        = False
        self.debug          = False
        self.report_key     = "ica"
        
        self._CFG           = jCFG(**kwargs)
        self._plot_dir      = None
        self._ics_found_svm = None
        self._report        = { "ICA-FI-AR":None,"ICA-AR":None }
        self._clear()
        
    #@property
    #def ICs(self): return self._ica_obj.exclude
  
    @property
    def stage(self): return self._stage
    @stage.setter
    def stage(self,v):
        self._stage=v
             
    @property
    def path(self): return self._raw_path
    @path.setter
    def path(self,v):
        if not v: return
        if jb.isPath(v):
           self._raw_path = v
        else:
            logger.exception("!!! No such path: {}".format(v))
            
    @property
    def path_ica(self): return os.path.join(self.path,"ica")
    @property
    def path_ica_chops(self): return os.path.join(self.path_ica,"chops")

    @property
    def plot_dir(self): return os.path.join(self.path,self.cfg.plot_dir)
    
    @property
    def raw(self): return self._raw

    @property
    def raw_fname(self): return self._raw_fname

    @raw_fname.setter
    def raw_fname(self,v):
        self._raw_fname = jb.isFile(v,path=self.path)

    @property
    def picks(self): return self._picks
    
    @property
    def CFG(self): return self._CFG
    @property
    def cfg(self): return self._CFG._data
    
    @property
    def report(self): return self._report

    def clear(self,objects=None):
    
        if isinstance(objects,(list)):
            while objects:
                try:
                    obj = objects.pop()
                    obj.close()
                    del obj
                except:
                    pass
    
        self.PreFilter.clear()
        self.Chopper.clear()
        self.ICAPerformance.clear()
        self._clear()
    
    def _clear(self):
        self._start_time = time.time()
        
        self._stage     = None
        self._path      = None
        self._path_ica  = None

        self._raw       = None
        self._raw_path  = None
        self._raw_fname = None
        self._raw_isfiltered = False
        
        self._ica_obj   = None
        self._picks     = None
        
        self._filter_prefix = ""
        self._filter_fname  = ""
        self._report        = { "ICA-FI-AR":None,"ICA-AR":None }
        
    def _update_from_kwargs(self,**kwargs):
        self._raw      = kwargs.get("raw",self._raw)
        self.path      = kwargs.get("path",self._path)
        self._stage    = kwargs.get("stage",self.stage)
        self.raw_fname = kwargs.get("raw_fname",self._raw_fname)
   
    def _set_ecg_eog_annotations(self):
        """
        finding ECG, EOG events in raw, setting events as anotations in raw
        """
       #--- find ECG in raw
        self.ICAPerformance.ECG.find_events(raw=self.raw,**self.CFG.GetDataDict("ecg"))
       #--- find EOG in raw
        self.ICAPerformance.EOG.find_events(raw=self.raw,**self.CFG.GetDataDict("eog"))
        
  
    def trunc_nd(self,n,d):
        """
        https://stackoverflow.com/questions/8595973/truncate-to-three-decimals-in-python/8595991
        """
        n = str(n)
        return (n if not n.find('.') + 1 else n[:n.find('.') + d + 1])
   
    def _initRawObj(self):
        """
        load or get RAW obj
        init & mkdir path tree  <stage>/../ica/chops
        init picks from RAW
        
        init report HDF file name
 
        """
        self._raw,self._raw_fname = jb.get_raw_obj(self.raw_fname,raw=self.raw)
    
        self._raw_path = os.path.dirname(self._raw_fname)
        if self.stage:
            self._raw_path = os.join(self.stage,self._raw_path)
        #---
        mkpath(self.path_ica_chops,mode=0o770)
    
        #--- get picks from raw
        self._picks = jb.picks.meg_nobads(self._raw)
    
    def _initChopper(self):
        cfg = self.cfg.chops
        self.Chopper.update(raw=self.raw,length=cfg.length,and_mask=cfg.and_mask,exit_on_error=cfg.exit_on_error,
                            description=cfg.description,time_window_sec=cfg.time_window,
                            show=cfg.show,verbose=self.verbose,debug=self.debug)

    def _initPreFilter(self):
        msg = []
        if self.cfg.pre_filter.run:
           cfg = self.cfg.pre_filter
           self.PreFilter.apply(
                   flow      = cfg.flow,
                   fhigh     = cfg.fhigh,
                   save      = cfg.save,
                   overwrite = cfg.overwrite,
                   raw       = self.raw.copy(),
                   picks     = self.picks,
                  # annotations = self.raw.annotations.copy()
                  )
           self.PreFilter.GetInfo(msg=msg)
           
        else:
           self.PreFilter.clear()
        
                 
    def _get_chop_name(self,raw,chop=None,extention=None,postfix=None,fullpath=False,chop_path=None):
        """
        raw
        chop     = None
        extention= "-ica.fif" [-raw.fif]
        postfix  = None      [ar]
        chop_path= None, path or use CLS var <path_ica_chops>
        fullpath = True
                   if True: includes path in filename
        Return:
        -------
        fname chop,fname orig
        """
        fname = jb.get_raw_filename(raw)
        fname,fextention = op.basename(fname).rsplit('-',1)
        
        chop_fix = ""
        
        if fullpath:
           if not chop_path:
              chop_path = self.path_ica_chops
           if fname.startswith(chop_path):
              fchop = fname
           else:
              fchop = op.join(chop_path,fname)
        else:
           fchop = fname
           
        try:
           if len(chop):
              if np.isnan(chop[1]):
                 chop_fix = ',{:04d}-{:04d}'.format(int(chop[0]),int(raw.times[-1]))
              else:
                 chop_fix = ',{:04d}-{:04d}'.format(int(chop[0]),int(chop[1]))
        except:
            pass

        if not fchop.endswith(chop_fix):
           fchop += chop_fix

        if postfix:
           if not fchop.endswith(postfix):
                fchop += "," +postfix

        if extention:
           fchop+= extention
        else:
           fchop+= "-"+fextention
    
        return fchop,fname
      
    def _apply_fit(self,raw_chop=None,chop=None,idx=None,save=False):
        """
        call to jumeg fit_ica
        raw_chop = None
        chop     = None
        save: save ica obj  <False>
        ToDo
        if not overwrite
          if ICA file exist: load ICA
          else calc ICA
        
        :return:
        ICA obj, ica-filename
        """
        ica_obj = None
        self._ics_found_svm = None

        fname_ica,fname = self._get_chop_name(raw_chop,extention="-ica.fif",chop=None)
      
        msg=["start ICA FIT chop: {} / {}".format(idx + 1,self.Chopper.n_chops),
             " --> chop id      : {}".format(chop),
             "  -> ica fname    : {}".format(fname_ica),
             "  -> ica chop path: {}".format(self.path_ica_chops),
             "  -> raw filename : {}".format(fname)
             ]
        logger.info("\n".join(msg))
        
       #--- ck for ovewrite & ICA exist
        load_from_disk = False
        if not self.cfg.fit.overwrite:
           load_from_disk = jb.isFile(fname_ica,path=self.path_ica_chops)
       
        if load_from_disk:
           # self._ica_obj,fname_ica = jb.get_raw_obj(fname_ica,path=self.path_ica_chops)
           ica_obj,fname_ica = jb.get_raw_obj(fname_ica,path=self.path_ica_chops)
        
           logger.info("DONE LOADING ICA chop form disk: {}\n  -> ica filename: {}".
                       format(chop,fname_ica))
        else:
            
            '''
            ToDO
            new def fit_ica
            -> mne ICA obj
            -> find ECG via annotation -> use CTPs or MNE
            -> find EOG via annotation
            '''
            if self.useArtifactRejection:
               # with jumeg_logger.StreamLoggerSTD(label="ica fit"):
               ica_obj = fit_ica(raw=raw_chop,picks=self.picks,reject=self.CFG.GetDataDict(key="reject"),
                                 ecg_ch=self.cfg.ecg.ch_name,ecg_thresh=self.cfg.ecg.thresh,
                                 flow_ecg=self.cfg.ecg.flow,fhigh_ecg=self.cfg.ecg.fhigh,
                                #---
                                  eog_hor = self.cfg.eog.hor_ch,
                                  eog_ver = self.cfg.eog.ver_ch,
                                  flow_eog=self.cfg.eog.flow,fhigh_eog=self.cfg.eog.fhigh,
                                  eog_thresh=self.cfg.eog.thresh,
                                #---
                                  use_jumeg=self.cfg.ecg.use_jumeg,
                                  random_state=self.cfg.random_state)
           
               # ica_obj.exclude = list( set( ica_obj.exclude ) )
               
            if self.useSVM:
               if not ica_obj:
                  logger.info('SVM start ICA FIT: init ICA object')
                 #--- !!! ToDo put parameter in CFG file
                  ica_obj = ICA(method='fastica',n_components=40,random_state=42,max_pca_components=None,
                                max_iter=5000,verbose=False)
                  ica_obj.fit(raw_chop,picks=self.picks,decim=None,reject=self.CFG.GetDataDict(key="reject"),
                                verbose=True)
               else:
                 logger.info('SVM ICA Obj start')
                #--- !!! do_copy = True => resample
                 ica_obj,_ = self.SVM.run(raw=self.raw,ICA=ica_obj,picks=self.picks,do_crop=False,do_copy=True)
                 logger.info('DONE SVM ICA FIT: apply ICA.fit')

        #-- save ica object
        if save and not load_from_disk:
           logger.info("saving ICA chop   : {} / {}\n".format(idx + 1,self.Chopper.n_chops) +
                       "  -> ica filename : {}".format(fname_ica))
           ica_obj.save(os.path.join(self.path_ica_chops,fname_ica))
              
        logger.info("done ICA FIT for chop: {}\n".format(chop)+
                    "  -> raw chop filename    : {}\n".format(fname_ica)+
                    "-"*30+"\n"+
                    "  -> ICs found JuMEG/MNE  : {}\n".format(self.SVM.ICsMNE)+
                    "  -> ICs found SVM        : {}\n".format(self.SVM.ICsSVM) +
                    "  -> ICs excluded         : {}\n".format(ica_obj.exclude)+
                    "-"*30+"\n"+
                    "  -> save ica fit         : {}".format(self.cfg.fit.save)
                   )
        
        return ica_obj,fname_ica
  
    def _apply_ica_artefact_rejection(self,raw,ICA,picks=None,reject=None):
        """
        Applies ICA to the raw object. (ica transform)

        Parameters
        ----------
            raw : mne.io.Raw()  (raw chop)
                     Raw object ICA is applied to
            ica : ICA object
                  ICA object being applied to the raw object
            picks: picks, <None>
            reject: MNE reject dict
            
        Returns
        -------
            raw_clean : mne.io.Raw()
                       Raw object after ICA cleaning
        """
        logger.info("Start ICA Transform => call <apply_ica_replace_mean_std>")
        
        if not picks:
            picks = self.picks
        return ica_artefact_rejection_and_apply(raw,ICA,picks=picks,reject=reject) #copy_raw=copy_raw,copy_ica=copy_ica
   
    def _update_report(self):
        """
        
        :param fimages:
        :return:
        """
      #--- update report config
        CFG = jCFG()
        report_config = os.path.join(self.plot_dir,os.path.basename(self.raw_fname).rsplit("_",1)[0] + "-report.yaml")
        d = None
        if not CFG.load_cfg(fname=report_config):
            d = { "ica": self.report }
        else:
            CFG.config["ica"] = self.report
        CFG.save_cfg(fname=report_config,data=d)

    def _plot_chop_performance(self,raw=None,ica=None,raw_clean=None,fout=None):
        """
        Args:
           raw:
           ica:
           raw_clean:
           fout:

        Returns:
           filename of plot with plot_dir
           result/007_TEST_200220_0220_2_c,rfDC,meeg,nr,bcc,int-ar.png

        """
        txt = "ICs JuMEG/MNE: "
        # ToDo ck SVM  => last ica_obj  ICs
        if self.useSVM:
           if self.SVM.ICsMNE:
              txt+= ",".join( [str(i) for i in self.SVM.ICsMNE ] )
              txt+= " SVM: {}".format(self.SVM.ICsSVM)
           else:
              txt+= ",".join( [str(i) for i in ica.exclude ] )
        return self.ICAPerformance.plot(raw=raw,raw_clean=raw_clean,verbose=True,text=txt,
                                        plot_path=self.plot_dir,fout=fout.rsplit("-",1)[0] + "-ar")
        #return os.path.basename(fout)
    
    def _save_chop(self,raw_chop,chop,fullpath=True,extention=None,postfix=None):
        """
        

        Parameters
        ----------
        raw_chop : TYPE
            DESCRIPTION.
        chop : TYPE
            DESCRIPTION.
        fullpath  : True
        extention : string, optional -raw.fif
        postfix   : string  optional ar

        Returns
        -------
        fname_chop : TYPE
            DESCRIPTION.

        """
        if self.debug:
           logger.debug("START save chop {} => {}".format(chop,jb.get_raw_filename(raw_chop) ))
        
        fname_chop,fname_raw = self._get_chop_name(raw_chop,chop=chop,fullpath=fullpath,extention=extention,postfix=postfix)
        
        jb.set_raw_filename(raw_chop,fname_chop)
        
        raw_chop.save(fname_chop,overwrite=True)
        if self.debug:
           logger.debug("DONE  save chop: {} => {}".format(chop,fname_chop))
           
        return fname_chop
        
    def _copy_crop_and_chop(self,raw,chop,extention="-raw.fif",save=False):
        """
        

        Parameters
        ----------
        raw : TYPE
            DESCRIPTION.
        chop : TYPE
            DESCRIPTION.
        extention : TYPE, optional
            DESCRIPTION. The default is "-raw.fif".
        save : TYPE, optional
            DESCRIPTION. The default is False.
     
        Returns
        -------
        raw_chop : TYPE
            DESCRIPTION.

        """
        raw_chop = self.Chopper.copy_crop_and_chop(raw,chop) # ck save chop
 
        if save:
           self._save_chop(raw_chop,chop,fullpath=True,extention=extention)
        else:
            fname_chop,fname_raw = self._get_chop_name(raw_chop,chop=chop,fullpath=True,extention=extention)
            jb.set_raw_filename(raw_chop,fname_chop)
        return raw_chop        
         
    def _concat_and_save(self,raw_chops,fname=None,annotations=None,save=False,ar_extention=",ar-raw.fif"):
        """
        concat and save raw chops
        
        Parameters
        ----------
        raw_chops : TYPE
            DESCRIPTION.
        fname : TYPE, optional
            DESCRIPTION. The default is None.
        annotations : TYPE, optional
            DESCRIPTION. The default is None.
        save : TYPE, optional
            DESCRIPTION. The default is False.
        ar_extention : TYPE, optional
            DESCRIPTION. The default is ",ar-raw.fif".
 
        Returns
        -------
        raw_clean : TYPE
            DESCRIPTION.
        fimages : TYPE
            DESCRIPTION.
        fimages_fi : TYPE
            DESCRIPTION.
 
        """
        if not fname.endswith(ar_extention):
           fname.replace("-raw.fif",ar_extention)
        return self.Chopper.concat_and_save(raw_chops,fname=fname,annotations=annotations,save=save)
        
    def _apply_chop_by_chop(self):
        """
        
        Returns:
          raw cleaned
        """
        raw_chops_clean_fi = []
        raw_chops_clean    = []
         
        plt_fnames    = []
        plt_fnames_fi = []  
        raw_clean     = None
        
        self.Chopper.verbose = True
        
        for idx in range(self.Chopper.n_chops):
            chop = self.Chopper.chops[idx]
            logger.info("Start ICA FIT & Transform chop: {} / {}\n".format(idx + 1,self.Chopper.n_chops))
           
            ica_obj   = None   
            fname_ica = None
            raw_cc    = None
            
           #-- ck for filter
            if self.PreFilter.isFiltered:
               opt = self.cfg.transform.filtered
              #-- chop raw filter  ToDo add option to save chop
               raw_chop = self._copy_crop_and_chop(self.PreFilter.raw,chop,extention="-raw.fif",save=opt.save)
              #-- calc filter ICA obj
               ica_obj,fname_ica = self._apply_fit(raw_chop=raw_chop,chop=chop,idx=idx,save=self.cfg.fit.save) # ck save ICA obj
            
               if self.cfg.transform.run and opt.run:
                  fout = jb.get_raw_filename(raw_chop)
               
                  raw_cc = self._apply_ica_artefact_rejection(raw_chop,ica_obj,reject=self.CFG.GetDataDict(key="reject") ) # raw_chop copy internal
               
                  if opt.save_chop_clean:
                     self._save_chop(raw_cc,chop,extention=',ar-raw.fif')
               
                  plt_fnames_fi.append(self._plot_chop_performance(raw=raw_chop,ica=ica_obj,raw_clean=raw_cc,
                                                                   fout=fout.rsplit("-",1)[0] + "-ar"))
                  
                  if opt.save:
                     raw_chops_clean_fi.append( raw_cc.copy() )
             
              #--- clean up for filter raw chop
               raw_chop.close()
               raw_chop = None
      
           #-- chop raw unfiltered
            opt = self.cfg.transform.unfiltered
           #-- chop raw filter 
            raw_chop = self._copy_crop_and_chop(self.raw,chop,extention="-raw.fif",save=opt.save)
            
            if not ica_obj:
               ica_obj,fname_ica = self._apply_fit(raw_chop=raw_chop,chop=chop,idx=idx,save=self.cfg.fit.save)
                
            if self.cfg.transform.run and opt.run:
               fout = jb.get_raw_filename(raw_chop)
               
               raw_chops_clean.append(self._apply_ica_artefact_rejection(raw_chop,ica_obj,reject=self.CFG.GetDataDict(key="reject")) ) # raw_chop copy internal

               if opt.save_chop_clean:
                   self._save_chop(raw_chops_clean[-1],chop,extention=',ar-raw.fif')

               plt_fnames.append(self._plot_chop_performance(raw=raw_chop,ica=ica_obj,raw_clean=raw_chops_clean[-1],
                                                             fout=fout.rsplit("-",1)[0] + "-ar"))
               
            logger.info("done ICA FIT & transform chop: {} / {}\n".format(idx + 1,self.Chopper.n_chops))
           
           #--- clean up for raw chop
            ica_obj = None
            raw_chop.close()
            raw_chop = None
           
            if raw_cc:
               raw_cc.close()
               raw_cc = None
        
        del(ica_obj)
       
       #--- concat & save raw chops filtered to raw_clean filtered
        if raw_chops_clean_fi:
           raw_clean_fi = self._concat_and_save(raw_chops_clean_fi,
                                                fname      = self.PreFilter.fname,
                                                annotations= self.PreFilter.raw.annotations,
                                                save       = self.cfg.transform.filtered.save)
            
           del( raw_chops_clean_fi )
           
           self.ICAPerformance.plot(raw=self.PreFilter.raw,raw_clean=raw_clean_fi,plot_path = self.plot_dir,
                                    text=None,fout = self.PreFilter.fname.rsplit("-",1)[0] + "-ar")
           self._report["ICA-FI-AR"] = [ os.path.basename(f) for f in [self.ICAPerformance.Plot.fout,*plt_fnames_fi]]
           raw_clean_fi.close()
           del( raw_clean_fi )
           
                  
       #--- concat & save raw chops to raw_clean
        if raw_chops_clean:
           fname = self.raw_fname.rsplit('-',1)[0]
           raw_clean = self._concat_and_save(raw_chops_clean,
                                             fname = fname + ",ar-raw.fif",
                                             annotations= self.raw.annotations,
                                             save  = self.cfg.transform.unfiltered.save)
           del( raw_chops_clean )             
       
        #-- plot
           self.ICAPerformance.plot(raw=self.raw,raw_clean=raw_clean,verbose=True,text=None,
                                    plot_path=self.plot_dir,fout=self.raw_fname.rsplit("-",1)[0] + "-ar")
           self._report["ICA-AR"] = [ os.path.basename(f) for f in [self.ICAPerformance.Plot.fout,*plt_fnames] ]
        
           return raw_clean
        
        return None
        
 #==== MAIN function
    def run(self,**kwargs):
        """
        
        :param kwargs:
        :return:
        raw_unfiltered_clean,raw_filtered_clean
        
        """
        self._clear()
        self._update_from_kwargs(**kwargs)
        
       #--- load config
        kwargs["useStruct"] = True
        self._CFG.update(**kwargs )
        self.useSVM               = self.cfg.fit.use_svm
        self.useArtifactRejection = self.cfg.fit.use_artifact_rejection
        
       #--- init or load raw
        self._initRawObj()
       #--- find & store ECG/EOG events in raw.annotations
        self._set_ecg_eog_annotations()
       #--- chop times
        self._initChopper()
       #--- prefilter
        msg = [
            "Apply ICA => FIT & Transform",
            "  -> filename      : {}".format(self._raw_fname),
            "  -> ica chop path : {}".format(self.path_ica_chops),
            "-" * 40,
            "  -> chops [sec]    : {}".format(self.Chopper.chops_as_string ),
            "  -> chops [indices]: {}".format(self.Chopper.indices_as_string ),
            "-" * 40
            ]
       
        logger.info("\n".join(msg) )
        
        self._initPreFilter()
        
        #-- apply ICA fit & transform
        raw_clean = self._apply_chop_by_chop()
        #-- update report yaml
        self._update_report()
        
        logger.info("DONE ICA FIT & Transpose\n"+
                    "  -> filename : {}\n".format( jb.get_raw_filename(raw_clean) )+
                    "  -> time to process :{}".format( datetime.timedelta(seconds= time.time() - self._start_time ) ))
      
       #-- check data shapes orig and transformed
        shapes=[self._raw._data.shape]
        labels=["raw original"]
     
        if raw_clean:
           shapes.append(raw_clean._data.shape)
           labels.append("raw unfiltered_clean")
                     
        if not self.Chopper.compare_data_shapes(shapes,labels):
           raise ValueError(" ERROR in chop & crop data: shapes not equal\n")
     
        self.clear()
        
        return raw_clean

def test1():
   #--- init/update logger
    jumeg_logger.setup_script_logging(logger=logger,logfile=True)
    
    stage = "$JUMEG_PATH_LOCAL_DATA/exp/MEG94T/mne"
    fcfg  = os.path.join(stage,"meg94t_config01.yaml")
    fpath = "206720/MEG94T0T2/130820_1335/2/"
    
    path = os.path.join(stage,fpath)
    raw_fname = "206720_MEG94T0T2_130820_1335_2_c,rfDC,meeg,nr,bcc,int-raw.fif"


    stage = "$JUMEG_PATH_LOCAL_DATA/exp/QUATERS/mne"
    fcfg  = os.path.join(stage,"jumeg_config.yaml") #""quaters_config01.yaml")
    fpath = "210857/QUATERS01/191210_1325/1"
    path = os.path.join(stage,fpath)
    raw_fname = "210857_QUATERS01_191210_1325_1_c,rfDC,meeg,nr,bcc,int-raw.fif"

    #stage = "${JUMEG_TEST_DATA}/mne"
    #fcfg = "intext_config01.yaml"
    
    raw = None
    #fpath = "211855/INTEXT01/190329_1004/6"
    #path = os.path.join(stage,fpath)
    # raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc-raw.fif"
    #raw_fname = "211855_INTEXT01_190329_1004_6_c,rfDC,meeg,nr,bcc,int-raw.fif"
    
    logger.info("JuMEG Apply ICA mne-version: {}".format(mne.__version__))
    #--
    jICA = JuMEG_PIPELINES_ICA()
    raw_unfiltered_clean,raw_filtered_clean = jICA.run(path=path,raw_fname=raw_fname,config=fcfg,key="ica")

    #raw_filtered_clean.plot(block=True)

if __name__ == "__main__":
    
  test1()
  
'''
    def _calc_chop_times(self):
        """
        calc chop times & indices

        Returns
        self._chop_times,self._chop_indices
        -------
        TYPE
            DESCRIPTION.

        """
        logger.debug("Start calc Chop Times: length: {} raw time: {}".format(self.cfg.chops.length,self.raw.times[-1]))
        
        self._chop_times   = None
        self._chop_indices = None
       
        #--- warn if times less than chop length
        if self.raw.times[-1] <= self.cfg.chops.length:
           logger.warning("<Raw Times> : {} smaler than <Chop Times> : {}\n\n".format(self.raw.times[-1],self._chop_times))
                       
        self._chop_times,self._chop_indices = get_chop_times_indices(self.raw.times,chop_length=self.cfg.chops.length) 
        
        if self.debug:
           logger.debug("Chop Times:\n  -> {}\n --> Indices:  -> {}".format(self._chop_times,self._chop_indices))
        
        return self._chop_times,self._chop_indices
        
       
    def _copy_crop_and_chop(self,raw,chop):
        """
        copy raw
        crop
        :param raw:
        :param chop:
        :return:
        """
        if self._chop_times.shape[0] > 1:
           raw_crop = raw.copy().crop(tmin=chop[0],tmax=chop[1])
           if self.debug:
              logger.debug("RAW Crop Annotation : {}\n  -> tmin: {} tmax: {}\n {}\n".format(jb.get_raw_filename(raw),chop[0],chop[1],raw_crop.annotations))
           return raw_crop
        return raw
'''
    