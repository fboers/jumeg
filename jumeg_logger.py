#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 18.03.19
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

from pprint import PrettyPrinter #,pprint,pformat

import sys,os,time,logging
import inspect
from logging.handlers import TimedRotatingFileHandler

# "%(asctime)s — %(name)s — %(levelname)s — %(funcName)s:%(lineno)d — %(message)s"

class JuMEG_LoggerFormatter(object):
    def __init__(self,**kwargs):
        super().__init__()
        self.info = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s - %(module)s - %(message)s")
        self.error= logging.Formatter("%(asctime)s — %(name)s — %(levelname)s - %(module)s - %(funcName)s:%(lineno)d — %(message)s")



class _FunctionInfoLogger(type):
    """
    https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
    
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_FunctionInfoLogger, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

  
     
class JuMEG_Logger_Base(metaclass=_FunctionInfoLogger):
   """
    logger cls
    :param: app_name => logger name <None>
    :param: level    => logging level  <10>
       level values:
        CRITICAL 50
        ERROR 	 40
        WARNING  30
        INFO 	 20
        DEBUG 	 10
        NOTSET 	 0
    
    https://realpython.com/python-logging/
    https://docs.python.org/3/howto/logging-cookbook.html
    https://stackoverflow.com/questions/44522676/including-the-current-method-name-when-printing-in-python
    
    Example:
    ---------
    from jumeg.jumeg_base import JuMEG_Logger
    myLog=JuMEG_Logger(app_name="MYLOG",level=logging.DEBUG)
    myLog.info( "test logging info instead of using <print> ")
    
    from jumeg.jumeg_base import JuMEG_Base_Basic as JB
    jb=JB()
    jb.Log.info("test logging info instead of using <print>")
    
    https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
    import logging
    logger = logging.getLogger('root')
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT)
    logger.setLevel(logging.DEBUG)
    
   """
   def __init__( self, **kwargs):
       super().__init__()
       self._logger = None
       self._name   = __name__
       self._LogFMT = JuMEG_LoggerFormatter()
       self._init(**kwargs)
   
   @staticmethod
   def __get_call_info():
       """
       https://stackoverflow.com/questions/10973362/python-logging-function-name-file-name-line-number-using-a-single-file
       """
       stack = inspect.stack()

       # stack[1] gives previous function ('info' in our case)
       # stack[2] gives before previous function and so on

       fn = stack[2][1]
       ln = stack[2][2]
       func = stack[2][3]

       return fn, func, ln
   
   @property
   def logger(self):
       if not self._logger:
          self._logger = logging.getLogger(self._name)
       return self._logger
   
   def _update_from_kwargs(self,**kwargs):
       self._name = kwargs.get("name",__name__)
       self._level= kwargs.get("level",logging.DEBUG)

   def _init(self,**kwargs):
       self._update_from_kwargs(**kwargs)
       self.init_logger()
      # self.verbose = False
       #self.logger = logging.getLogger(self._name)
       #self.logger.setLevel(self._level)
       
       #self.fmt_info  = 'JuMEG LOG %(asctime)s %(message)s'
       #logging.basicConfig(format=self.fmt_info,datefmt='%Y/%m/%d %I:%M:%S')
       
       #self.fmt_debug   = '%(asctime)-15s] %(levelname) %(funcName)s %(message)s'
       #self.fmt_error   = '[%(asctime)-15s] [%(levelname)08s] (%(funcName)s %(message)s'
       #formatter = logging.Formatter("%(asctime)s - %(name)s - %(message)s")
   
       # https://www.toptal.com/python/in-depth-python-logging
   
   def init_logfile_name(self,experiment="test",module="module",postfix="001",extention=".log"):
       """
       module, experiment,user ,datetime
       get path
       
       ${JUMEG_LOG_FILE_PATH}
       <experiment>_<script name>_<user>_<date-time>_<index>
       M100_epocher_meguser_2019-03-18-10-01-01_001.log
       :param kwargs:
       :return:
       """
       
       fn = experiment+"_"+module+"_"+os.getenv("USER","meg")+"_"+ time.strftime("%G-%m-%d %H:%M:%S",time.localtime())+"_"+postfix+ extention
       fn = fn.replace(" ","_").replace(":","-")
       #print("log file: "+fn)
       return fn
   
   def _init_console_handler(self,name="console",fmt=None,level=None):
       """
       ToDO set differenr formatter for LogLevels and create new Handlers
       :param kwargs:
       :return:
       """
       if not fmt:
          fmt=self._LogFMT
       if not level:
           level= self._level
           
       CH = logging.StreamHandler(sys.stdout)
       CH.setFormatter(fmt)
       CH.setLevel(level)
       CH.set_name(name)
       return CH
   
   def _init_file_handler(self,name="file",fmt=None,level=None):
       if not fmt:
           fmt = self._LogFMT
       if not level:
           level = self._level
    
       FH = TimedRotatingFileHandler(self.init_logfile_name(), when='midnight')
       FH.setFormatter(fmt)
       FH.setLevel(level)
       FH.set_name(name)
       return FH
   
   def init_logger(self,**kwargs):
       """
       overwrite
       :param kwarg:
       :return:
       """
       self.logger.setLevel(self._level)
       self.logger.addHandler(self._init_console_handler(name="ch_info",fmt=self._LogFMT.info,level=self._level))
       self.logger.addHandler(self._init_console_handler(name="ch_error",fmt=self._LogFMT.error,level=40))
       self.logger.addHandler(self._init_file_handler(name="fh_info",fmt=self._LogFMT.info))
     
     # with this pattern, it's rarely necessary to propagate the error up to parent
       self.logger.propagate = False
       return self.logger
   
   def list2str(self,msg):
       """ __str__()"""
       
       #if isinstance(msg,(list)):
       #   return "\n"+"\n".join(msg)
       return msg.__str__()
   
   def info( self,msg ):
       #self.logger.setFormatter()
       self.logger.info( self.list2str(msg) )

   def debug(self,msg):
       self.logger.debug(self.list2str(msg),exc_info=True)

   def warning( self,msg ):
       self.logger.warning(self.list2str(msg) )
       
   def error( self,msg):
       if isinstance(msg,(list)):
          self.logger.error("\nERROR:\n"+self.list2str(msg)+"\n",exc_info=True)
       else:
          msg+="\n-> "+ str(sys._getframe(0))+"\n"
          msg+="-> "+ str(sys._getframe(0).f_code.co_filename)
          msg+="\n--> "+ str(sys._getframe(1))+"\n"
          msg+="--> "+ str(sys._getframe(1).f_code.co_filename)
          #msg += "\n---> " + str(sys._getframe(2)) + "\n"
          #msg += "---> " + str(sys._getframe(2).f_code.co_filename)

          self.logger.error("\nERROR: "+msg+"\n",exc_info=True,)
       
       
   def error1(self, message, *args):
        message = "{} - {} at line {}: {}".format(*self.__get_call_info(), message)
        self.logger.error(message, *args)

       
      # if self.verbose:
      #    traceback.print_exc()
   def critical( self, msg ):
       self.logger.critical( self.list2str(msg),exc_info=True )

   def exception(self, msg, *args, exc_info=True, **kwargs):
       self.logger.exception(self.list2str(msg), *args, exc_info=True, **kwargs)

 


class JuMEG_Logger(JuMEG_Logger_Base):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
    
    def init_logger(self):
       """
       add you Handlers
       :return:
       """
       self.logger.setLevel(self._level)
       self.logger.addHandler(self._init_console_handler(name="ch_info",fmt=self._LogFMT.info,level=self._level))
       self.logger.addHandler(self._init_console_handler(name="ch_error",fmt=self._LogFMT.error,level=40))
       self.logger.addHandler(self._init_file_handler(name="fh_info",fmt=self._LogFMT.info))
     
     # with this pattern, it's rarely necessary to propagate the error up to parent
       self.logger.propagate = False
       return self.logger
  
    
    
#=========================================================================================
#==== MAIN
#=========================================================================================
def main():
    log = JuMEG_Logger( name="TESTLOG",level=10)
    log.info("TEST info")
    log.debug("TEST debug")
    log.warning("TEST warnings")
    log.error("TEST error")
    log.error1("TEST error1")
    log.critical("TEST critical")
 
    import numpy as np
    a=np.arange(10)
    log.warning(a)
    
   
if __name__ == "__main__":
   main()
