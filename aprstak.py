#!/usr/bin/python -u

import logging
import time
#from time import sleep,gmtime,strftime
import os
import sys, getopt
import socket
import uuid


from sys import version_info
import json
from  xml.dom.minidom import parseString

import aprslib

#import xml.etree.ElementTree as ET

# Bail if not python 3 or later
#if sys.version_info.major < 3:
if version_info.major < 3:
    print("Must use python 3 or later")
    exit()

# Setup Logging
DEFAULT_LEVEL = logging.WARNING

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
aprs_reportsmax = 10000

# Filter values for the APRS Feed
filter_range = "300"
# Atlanta (SE US)
filter_lat = "33.98"
filter_lon = "-84.650"
# center of the US
#filter_lat = "39.8283"
#filter_lon = "-98.5795"
filter_type = " -t/oimqstunw"

# or US wide filter
#filter_text="a/50/-130/20/70" + filter_type
# Eastern US
#filter_text="a/66/-98.6/20/70" + filter_type


# APRS server, should use the load balancing ones
#host = "noam.aprs2.net"
#port = "14580"

# Setup the aprs.is filter string
filter_text="r/" + filter_lat + "/" + filter_lon + "/" + filter_range + filter_type

# or US wide filter
filter_text_us="a/50/-130/20/70" + filter_type
# Eastern US
filter_text_eus="a/66/-98.6/20/70" + filter_type

# APRS Login info, -1 for password means read only
aprs_user = "KM4BA-TS"
aprs_password = "-1"

# APRS server, should use the load balancing ones
#host = "noam.aprs2.net"
#port = "14580"


server = ""
#debug = False
# get the args
argv=sys.argv[1:]

# now parse
try:
    opts, args = getopt.getopt(argv,"lfdD",["debug=","max=","range=","eastus"])
except getopt.GetoptError:
    print ('aprstak.py -l or -f or -d')
    sys.exit(2)

for opt, arg in opts:
    if opt == '-l':
        server="local"
    #elif opt in ("-i", "--ifile"):
    elif opt == '-f':
        server="fts"
    elif opt == '-d':
        server="discord"
    if opt == "-D":
        print("DEBUG selected")
        DEFAULT_LEVEL = logging.DEBUG
        logger.setLevel(DEFAULT_LEVEL)
    elif opt == "--debug":
        if arg == "DEBUG":
            logger.debug("DEBUG selected")
            DEFAULT_LEVEL = logging.DEBUG
        elif arg == "INFO":
            logger.debug("INFO selected")
            DEFAULT_LEVEL = logging.INFO
        logger.setLevel(DEFAULT_LEVEL)
    elif opt == "--max" and int(arg) > 0:
        aprs_reportsmax = int(arg)
    elif opt == "--range" and int(arg) > 0:
        filter_range = int(arg)
        logger.debug("Filter range set to: " + arg)
        filter_text="r/" + filter_lat + "/" + filter_lon + "/" + filter_range + filter_type
    elif opt == "--eastus":
        filter_text = filter_text_eus
        logger.debug("Filter to: " + filter_text)

if not server:
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
                    

    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        logger.debug("APRS parse failed:" + str(packet))
        aprs_source = ""
        pass
        return 

    except:
        logger.debug("APRS parse failed other error:" + str(packet))
        aprs_source = ""
        pass
        return 

    #logger.setLevel(logging.DEBUG)
    logger.setLevel(DEFAULT_LEVEL)
    # Now try to make the CoT -------------------------------------------
    try:
        if aprs_source and aprs_lat and aprs_lon:
            # see if it's a real user
            #if aprs_source.startswith("K"):
            #    aprs_source = "KM4BA"
            if aprs_source in (x[0] for x in users):
                logger.debug("User " + aprs_source + " found in users list")
                for i in range(0,len(users)):
                    logger.debug("checking: " + users[i][0] + " " + users[i][1] + " " +  users[i][2])
                    if users[i][0] == aprs_source:
                        aprs_uid = users[i][1]
                        aprs_team = users[i][2]
                        aprs_icon = ""
                        aprs_point = False
                        logger.debug("Match: " + aprs_source + " " + aprs_uid + " " +  aprs_team)
                        break
                    else:
                        #logger.debug("User: " + users[i][0] + " not found")
                        pass
                logger.debug("User: " + aprs_source + " " + aprs_uid + " " +  aprs_team + " ---------")
            else:
                # not a real user, so set an icon instead
                #aprs_uid=aprs_source + str(uuid.uuid1())
                aprs_uid=aprs_source
                #aprs_team="Cyan"
                #aprs_source=""
                aprs_team =""
                aprs_icon ='f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/placemark_circle.png'
                aprs_point = True
                logger.debug("station: " + aprs_source + " " + aprs_uid + " " +  aprs_team + " ---------")

            #cot_xml = injectCoT.inject_cot(aprs_source, aprs_lat, aprs_lon, aprs_alt)
            try:
                # create the CoT from the info
                cot_xml = mkcot.mkcot(
                    cot_callsign=aprs_source
                    , cot_id=aprs_uid
                    , team_name=aprs_team
                    , cot_lat=aprs_lat
                    , cot_lon=aprs_lon
                    , cot_hae=aprs_alt
                    , cot_how="h-g-i-g-o"
                    #, cot_type="a" # not needed, default
                    , cot_identity="friend"
                    , cot_dimension="land-unit"
                    , cot_typesuffix="E-C-V"
                    , iconpath=aprs_icon
                    , cot_point=aprs_point
                    )
            except:
                logger.debug("mkcot failed")
        else:
            logger.info("Not useful APRS: " + packet)
            pass
    except:
        logger.debug("CoT creation failed: " +packet)
        cot_xml=""
        return  

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
            return 

    #logger.setLevel(logging.DEBUG)
    if cot_xml:
        try:

            # flush any pending server responses
            takserver.flush()

            # send the CoT string, server does not echo
            takserver.send(cot_xml)

            # flush any server responses
            takserver.flush()

            # Now log the report by type
            #if sleeptime > 0.1:
            if True and aprs_source and aprs_lat and aprs_lon:
                if aprs_point:
                    logger.info("Station: " + aprs_source 
                        + " Lat:" + aprs_lat + " Lon:" + aprs_lon + " Alt:" + aprs_alt
                        #+ " Speed:" + aprs_speed + " Course:" + aprs_course 
                        + " Counter: " + str(aprs_reports)
                        )
                else:
                    logger.info("User:    " +  aprs_source 
                        + " Lat:" + aprs_lat + " Lon:" + aprs_lon + " Alt:" + aprs_alt
                        #+ " Speed:" + aprs_speed + " Course:" + aprs_course 
                        + " Counter: " + str(aprs_reports)
                        )
            else:
                logger.debug("APRS not useful")

        except:
             logger.warning("APRS CoT push to server failed")


    # Increment the report count            
    aprs_reports += 1

    #logger.debug("End of callback processing -----------------------------------")
    if aprs_reports > aprs_reportsmax:
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
            takserver.close()
            time.sleep(0.5)
            logger.debug(server + " Closed")
        except:
            logger.warning(server + " close failed")
            pass

        logger.debug("Opening TAK Server " + server + " " + TAK_IP + ":" + str(TAK_PORT))
        try:
            # Now open server
            try:
                testsock = takserver.open(TAK_IP,TAK_PORT)
            except:
                logger.warning(server + " reopen failed")

            logger.debug("send a takserver connect")
            try:
                takserver.flush()  # flush the xmls the server sends (should not be any)

                # send the connect string, server does not echo
                takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign))
                logger.warning("Server " + server + " reconnected -------------------------------------")
                aprs_reports = 1
            except:
                logger.warning("Server " + server + " connect failed")

        except:
            logger.warning(server + " Reopen failed")



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
try:
    takserver.send(mkcot.mkcot(cot_type="t", cot_how="h-g-i-g-o", cot_callsign=my_callsign))
except:
    logger.error("Connect to TAK server failed")
    exit(1)

logger.info("TAK Server connected: " + server + " " + TAK_IP + ":" + str(TAK_PORT) )


lastcycle = time.time()

while True:
    try:
        logger.debug("Connecting to APRS.is")
        # Setup APRS Connection and connect
        # host should be rotate.aprs.net or similar
        AIS = aprslib.IS(aprs_user, passwd=aprs_password, host="second.aprs.net", port=14580)
        AIS.connect()
        logger.info("Connected to APRS.is")
    except:
        logger.error("APRS Connect failed")
        # Sleep for a bit if failed
        time.sleep(57)
        break

    # Filter and setup callback
    try:
        AIS.set_filter(filter_text)
    except:
        logger.error("APRS filter failed")
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
