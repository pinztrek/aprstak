#!/usr/bin/python -u

import aprslib
import logging
import time
#from time import sleep,gmtime,strftime
import os
import socket
import uuid

import injectCoT
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
#DEFAULT_LEVEL = logging.DEBUG

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


sleeptime = 0.075
aprs_reportsmax = 500
aprs_reportsmax = 10000

# Filter values for the APRS Feed
filter_range = "1200"
filter_range = "300"
# Atlanta (SE US)
filter_lat = "33.98"
filter_lon = "-84.650"
# center of the US
#filter_lat = "39.8283"
#filter_lon = "-98.5795"
filter_type = " -t/oimqstunw"

# Setup the filter string

filter_text="r/" + filter_lat + "/" + filter_lon + "/" + filter_range + filter_type

# or US wide filter
#filter_text="a/50/-130/20/70" + filter_type
# Eastern US
#filter_text="a/66/-98.6/20/70" + filter_type

# APRS Login info, -1 for password means read only
aprs_user = "KM4BA-TS"
aprs_password = "-1"

# APRS server, should use the load balancing ones
#host = "noam.aprs2.net"
#port = "14580"


# select a server, default to local
server = input('Server? local is default, "FTS" or "DISCORD" uses those public servers: ')
server = server.upper()

if server.startswith("F"):
    TAK_IP = os.getenv('TAK_IP', '204.48.30.216')
    TAK_PORT = int(os.getenv('TAK_PORT', '8087'))
    server = "FTS"

elif server.startswith("D"):
    TAK_IP = os.getenv('TAK_IP', '128.199.70.11')
    TAK_PORT = 48088
    server = "DISCORD"
else:
    # use the local server for default
    TAK_IP = '172.16.30.30'
    TAK_PORT = 8087
    server = "Local"

logger.debug(server + " Server selected " + TAK_IP + ":" + str(TAK_PORT))

#open the users list
userfile = 'users.json'
try:
    f = open(userfile, "r+")
    try:
        users = json.load(f)
        logger.info("Initial Users loaded")
        logger.debug(users)
    except:
        logger.warning("users json load failed")
        users = []
    finally:
        f.close()
except:
    users = []
    logger.warning("Users file open failed, resetting")

# initialize aprs_reports
aprs_reports = 1


def callback(packet):
    global aprs_reports
    global aprs_reportsmax
    global lastcycle
    global taksock

    #if PAUSE:
    #    return()

    #logger.debug("Callback: " + str(packet))
    #logger.setLevel(logging.WARNING)
    logger.setLevel(DEFAULT_LEVEL)
    try: 
        aprs_atoms = aprslib.parse(packet)
        aprs_format = aprs_atoms["format"]
        logger.debug("APRS format: " + str(aprs_format))
        if (aprs_format == "beacon"):
            #print("beacon skipped:" + str(packet))
            aprs_source = ""
            pass # Skip the rest
            return

        else:    
            #print(aprs_atoms)
            try:
                aprs_source = aprs_atoms["from"]
            except:
                logger.debug("No APRS From")
                aprs_source = ""
            try:
                aprs_lat = str(round(aprs_atoms["latitude"],5))
                aprs_lon = str(round(aprs_atoms["longitude"],5))
            except:
                logger.debug(aprs_source + " No Lat/Lon")
                aprs_lat = ""
                aprs_lon = ""
                next
            try:	
                aprs_alt = round(aprs_atoms["altitude"],0)
                if (aprs_alt <0):
                    aprs_alt = 0
                aprs_alt = str(aprs_alt)
            except:
                #print("No Altitude")
                aprs_alt = "9999999.0"

            # placeholders
            #aprs_speed = 0
            #aprs_course = 0
                    
            #print(aprs_source + " " + str(aprs_lat) + " " + str(aprs_lon) + " " + str(aprs_alt))
            #if sleeptime > 0.1:
            if True and aprs_source:
                #print("Log the report")
                logger.info(aprs_source 
                    + " Lat:" + aprs_lat + " Lon:" + aprs_lon + " Alt:" + aprs_alt
                    #+ " Speed:" + aprs_speed + " Course:" + aprs_course 
                    + " Counter: " + str(aprs_reports)
                    )
            elif aprs_source:
                logger.debug(aprs_source 
                    + " Lat:" + aprs_lat + " Lon:" + aprs_lon + " Alt:" + aprs_alt
                    #+ " Speed:" + aprs_speed + " Course:" + aprs_course 
                    + " Counter: " + str(aprs_reports)
                    )
                if int(aprs_reports % 10) == 0:
                    print("+", end="", flush=True)
                else:
                    #print(".", end="", flush=True)
                    pass
            else:
                logger.debug("APRS not useful")

    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        logger.debug("APRS parse failed:" + str(packet))
        aprs_source = ""
        pass
        #return 0 

    except:
        logger.debug("APRS parse failed other error:" + str(packet))
        aprs_source = ""
        pass
        #return 0 

    #logger.setLevel(logging.DEBUG)
    logger.setLevel(DEFAULT_LEVEL)
    try:
            if False:
                aprs_uid=user_uid
            else:
                aprs_uid=aprs_source + str(uuid.uuid1())

            #cot_xml = injectCoT.inject_cot(aprs_source, aprs_lat, aprs_lon, aprs_alt)
            if aprs_source and aprs_lat and aprs_lon:
                cot_xml = mkcot.mkcot(
                    cot_callsign=aprs_source
                    , cot_id=aprs_uid
                    , cot_lat=aprs_lat
                    , cot_lon=aprs_lon
                    , cot_hae=aprs_alt
                    , cot_how="h-g-i-g-o"
                    #, cot_type="a" # not needed, default
                    , cot_identity="friend"
                    , cot_dimension="land-unit"
                    , cot_typesuffix="E-C-V"
                    )
            else:
                logger.info("Not useful APRS: " + packet)
                pass
    except:
        logger.debug("mkcot failed")
        #logger.info("mkcot failed: " +packet)
        cot_xml=""
        #return 0 

    if cot_xml:
        try:
            my_xml = cot_xml.decode('utf-8')
            my_xml = parseString(str(my_xml.replace("\n","")))
            xml_pretty_str = my_xml.toprettyxml()

            logger.debug("CoT: " + aprs_source)
            logger.debug("CoT XML is: " + xml_pretty_str)
        except:
            cot_xml=""
            logger.debug("XML parse failed")
            #return 0 

    logger.setLevel(logging.DEBUG)
    if cot_xml:
        try:

            # flush any pending server responses
            takserver.flush()

            # send the CoT string, server does not echo
            takserver.send(cot_xml)

            # flush any server responses
            takserver.flush()

        except:
             logger.warning("APRS CoT push to server failed")


    #logger.debug("End of callback processing -----------------------------------")
    if aprs_reports >= aprs_reportsmax:
        try:    
            #print("aprs_reports:" + str(aprs_reports))
            cycletime = int(time.time() - lastcycle)
            lastcycle = time.time()
            logger.debug( "Close and Reopen the TAK connection " + str(aprs_reports) + " reports "
                + time.strftime("%d/%m/%y %H:%M:%S ", time.gmtime()))
            #print( "Close and Reopen the TAK connection " )
            #print( str(aprs_reportsmax / cycletime ) + " Reports / sec")
            logger.debug( str(round(aprs_reportsmax / cycletime, 2 )) + " Reports / sec")

        except:
            logger.debug("Reopen Stat Calc failed")
            
        try:
            logger.debug("Attempting Close")
            takserver.close()
            print( "FTS server socket closed")
            time.sleep(0.5)
        except:
            logger.warning(server + " close failed")
            pass

        logger.debug("Opening TAK Server " + server + "- " + TAK_IP + ":" + TAK_PORT)
        try:
            # Now open server
            testsock = takserver.open(TAK_IP,TAK_PORT)

            logger.debug("send a takserver connect")
            takserver.flush()  # flush the xmls the server sends (should not be any)

            # send the connect string, server does not echo
            connect_xml= mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign)
            print(connect_xml)
            #takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign))
            takserver.send(connect_xml)

            logger.info("Server " + server + " connected")
        except:
            logger.warning(server + " Reopen failed")

    aprs_reports += 1
                


#-----------------------------------------------------------------------------------------
# Main Program

# Setup a UID
my_uid = str(socket.getfqdn())
my_uid = my_uid + "-" + str(uuid.uuid1())
#my_uid = bytes("APRS_inject-" + my_uid,"UTF-8")
my_uid = ("APRS_inject-" + my_uid)
#print(my_uid)

taksock="" # this is a global

# Setup a callsign for the main process
my_callsign = "APRS-" + my_uid[-6:]
logger.debug("Callsign: " + str(my_callsign))

# substantiate the class
takserver = takcot()

# Now open server
logger.debug("Opening TAK Server " + server + "----------------------------------------------------")
testsock = takserver.open(TAK_IP,TAK_PORT)

logger.debug("send a takserver connect")
takserver.flush()  # flush the xmls the server sends (should not be any)

#connect_xml = mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", ", cot_callsign=my_callsign)

#my_xml = connect_xml.decode('utf-8')
#my_xml = parseString(str(my_xml.replace("\n","")))
#xml_pretty_str = my_xml.toprettyxml()

#logger.debug("Connect XML is: " + xml_pretty_str)

# send the connect string, server does not echo
takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign))

logger.info("Server " + server + " connected")

# Now open the socket the ATAK Server
#sock = 0
#while sock == 0:
    #print("Opening TAK Server")
    #sock = openTCP(ATAK_IP, ATAK_PORT)
    # Sleep for a bit if the open failed
    #if sock == 0:
        #time.sleep(57)
    

lastcycle = time.time()

while True:
    try:
        print("Connecting to APRS.is")
        # Setup APRS Connection and connect
        # host should be rotate.aprs.net or similar
        AIS = aprslib.IS(aprs_user, passwd=aprs_password, host="second.aprs.net", port=14580)
        AIS.connect()
    except:
        print("APRS Connect failed")
        # Sleep for a bit if failed
        time.sleep(57)
        break

    # Filter and setup callback
    try:
        AIS.set_filter(filter_text)
    except:
        print("APRS filter failed")
        break

    try:
        # Setup callback for APRS Packets
        AIS.consumer(callback, raw=True)
        logger.debug("AIS Consumer exited")
    except:
        print("APRS consumer failed")

        # Sleep for a bit if failed
        exit()
        time.sleep(11)
