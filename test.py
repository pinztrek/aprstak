#!/usr/bin/python -u

import aprslib
import logging
import time
#from time import sleep,gmtime,strftime
import os
import socket
import uuid

#import CoT

from sys import version_info
import json
from  xml.dom.minidom import parseString

#import xml.etree.ElementTree as ET

# Bail if not python 3 or later
#if sys.version_info.major < 3:
if version_info.major < 3:
    print("Must use python 3 or later")
    exit()

# Setup Logging
DEFAULT_LEVEL = logging.INFO
DEFAULT_LEVEL = logging.DEBUG

LOGGERFORMAT = '%(asctime)s %(message)s'
logging.basicConfig(
    format=LOGGERFORMAT
    , level=logging.INFO
    , datefmt='%m/%d/%Y %I:%M:%S')

logger = logging.getLogger(__name__)

# Seset the default logging level
logger.setLevel(DEFAULT_LEVEL)

#import takcot. Note this only works if you have installed the package
#   If you have not installed as a package, you may have to tune your imports
#   to be local to where your source is
from takpak.mkcot import mkcot
from takpak.takcot import takcot



# select a server, default to local
# use the local server for default
TAK_IP = '172.16.30.30'
TAK_PORT = 8087
server = "Local"

logger.debug(server + " Server selected " + TAK_IP + ":" + str(TAK_PORT))

#-----------------------------------------------------------------------------------------
# Main Program


#taksock="" # this is a global


# substantiate the class
takserver = takcot()

# Now open server
logger.debug("Opening TAK Server " + server + "----------------------------------------------------")
try:
    testsock = takserver.open(TAK_IP,TAK_PORT)
except:
    print("open failed")

logger.debug("send a takserver connect")
takserver.flush()  # flush the xmls the server sends (should not be any)

# send the connect string, server does not echo
takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign="KM4BA"))

logger.info("Server " + server + " connected")

time.sleep(1)
takserver.close()
logger.info("Server " + server + " closed")

time.sleep(20)

# Now open server
logger.debug("Opening TAK Server " + server + "----------------------------------------------------")
testsock = takserver.open(TAK_IP,TAK_PORT)

logger.debug("send a takserver connect")
takserver.flush()  # flush the xmls the server sends (should not be any)

# send the connect string, server does not echo
takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign))

logger.info("Server " + server + " connected")

time.sleep(1)
takserver.close()
logger.info("Server " + server + " closed")
