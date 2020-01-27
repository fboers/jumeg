#!/usr/bin/env python3
# -+-coding: utf-8 -+-

"""
"""

#--------------------------------------------
# Authors: Frank Boers <f.boers@fz-juelich.de> 
#
#-------------------------------------------- 
# Date: 08.01.20
#-------------------------------------------- 
# License: BSD (3-clause)
#--------------------------------------------
# Updates
#--------------------------------------------


# https://dev.to/goyder/automatic-reporting-in-python---part-1-from-planning-to-hello-world-32n1

# https://plot.ly/python/v3/html-reports/

# https://plot.ly/python/v4-migration/

import os
from jinja2 import FileSystemLoader, Environment

path= os.path.dirname( __file__)

# Content to be published
content = "Hello, world!"

# Configure Jinja and ready the template
env = Environment(
    loader=FileSystemLoader(searchpath="templates")
)
template = env.get_template(path+"/report.html")


def main():
    """
    Entry point for the script.
    Render a template and write it to file.
    :return:
    """
    with open("outputs/report.html", "w") as f:
        f.write(template.render(content=content))


if __name__ == "__main__":
    main()

