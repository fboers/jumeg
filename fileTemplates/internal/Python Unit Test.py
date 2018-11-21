#!/usr/bin/env python3
# -+-coding: utf-8 -+-
#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
# Date: ${DATE}
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Update
#--------------------------------------------

import unittest

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)

if __name__ == '__main__':
    unittest.main()
