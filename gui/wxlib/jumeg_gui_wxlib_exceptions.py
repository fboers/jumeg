#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
JuMEG Exception CLS for JuMEG GUI Excetion Messages

https://www.programiz.com/python-programming/user-defined-exception
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 17.12.18
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------

__version__='2018-12-17.001'

import wx
from   wx.lib.pubsub import pub

 
class JuMEG_GUIExceptionBase(Exception):
   """Base class for other exceptions"""
   pass

class MyError(Exception):
  
    # Constructor or Initializer
    def __init__(self, value):
        self.value = value
  
    # __str__ is to print() the value
    def __str__(self):
        return(repr(self.value))
  
try:
    raise(MyError(3*2))
  
# Value of Exception is stored in error
except MyError as error:
    print('A New Exception occured: ',error.value)
 
 
 class Networkerror(RuntimeError):
    def __init__(self, arg):
        self.args = arg
  
try:
    raise Networkerror("Error")
  
except Networkerror as e:
    print (e.args)
 



class AppError(Exception): pass

class MissingInputError(AppError):
  # define the error codes & messages here
    em = {1101: "Some error here. Please verify.", \
          1102: "Another here. Please verify.", \
          1103: "One more here. Please verify.", \
          1104: "That was idiotic. Please verify."}
 
 try:
    # do something here that calls
    # raise MissingInputError(1101)

except MissingInputError, e
    print "%d: %s" % (e.args[0], e.em[e.args[0]])
 
 
 
 
class CustomError(Exception):
"""
Custom Exception

https://stackoverflow.com/questions/6180185/custom-python-exceptions-with-error-codes-and-error-messages
"""

  def __init__(self, error_code, message='', *args, **kwargs):

      # Raise a separate exception in case the error code passed isn't specified in the ErrorCodes enum
      if not isinstance(error_code, ErrorCodes):
          msg = 'Error code passed in the error_code param must be of type {0}'
          raise CustomError(ErrorCodes.ERR_INCORRECT_ERRCODE, msg, ErrorCodes.__class__.__name__)

      # Storing the error code on the exception object
      self.error_code = error_code

      # storing the traceback which provides useful information about where the exception occurred
      self.traceback = sys.exc_info()

      # Prefixing the error code to the exception message
      try:
          msg = '[{0}] {1}'.format(error_code.name, message.format(*args, **kwargs))
      except (IndexError, KeyError):
          msg = '[{0}] {1}'.format(error_code.name, message)

      super().__init__(msg)


# Error codes for all module exceptions
@unique
class ErrorCodes(Enum):
    ERR_INCORRECT_ERRCODE = auto()      # error code passed is not specified in enum ErrorCodes
    ERR_SITUATION_1 = auto()            # description of situation 1
    ERR_SITUATION_2 = auto()            # description of situation 2
    ERR_SITUATION_3 = auto()            # description of situation 3
    ERR_SITUATION_4 = auto()            # description of situation 4
    ERR_SITUATION_5 = auto()            # description of situation 5
    ERR_SITUATION_6 = auto()            # description of situation 6
 
 
 if not <some_test>:
        raise AssertionError(<message>)
 
 assert <some_test>, <message>
 
          try:
              with open(fjson, "w") as f:
                   f.write(json.dumps(data,indent=4))
              f.close()
              wx.LogMessage("done saving template file: " + fout)
          except Exception as e:
              wx.LogError("Save failed!\n" + jb.pp_list2str(e,head="Error writing template file: "+fout) )
              pub.sendMessage("MAIN_FRAME.MSG.ERROR",data="Error writing template file: "+fout)
              raise
          finally: