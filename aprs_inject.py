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

logging.basicConfig(level=logging.INFO) # level=10

# Filter values for the APRS Feed
filter_range = "1200"
# Atlanta (SE US)
filter_lat = "33.98"
filter_lon = "-84.650"
# center of the US
#filter_lat = "39.8283"
#filter_lon = "-98.5795"
filter_type = " -t/oimqstunw"

sleeptime = 0.075
aprs_reportsmax = 500

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

ATAK_IP = '172.16.30.30'
ATAK_PORT = 8087

#ATAK_IP = os.getenv('ATAK_IP', '204.48.30.216')
#ATAK_PORT = int(os.getenv('ATAK_PORT', '8087'))

# initialize aprs_reports
aprs_reports = 1


def openTCP(ip_address, port):
    print("Opening:" + ip_address + ":" + str(port))
    try:
        mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn = mysock.connect((ip_address, port))
    except:
        print("Cannot connect to " + str(ip_address) + ":" + str(port))
        mysock = 0
        #exit()
    return mysock
    
def closeTCP(mysock):
    try:
        closereturn = mysock.shutdown(1)
        time.sleep(0.2)
        closereturn = mysock.close()
    except:
        closereturn = 0
        print("Socket Close failed")
    return closereturn

def pushTCP(mysock, cotdata):
    #cotdata =  b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<event version="2.0" uid="Bogon-H5NPCV052844VSE" type="a-f-G-E-V-C" time="2020-07-15T13:53:32.463Z" start="2020-07-15T13:53:32.463Z" stale="2020-07-15T13:59:47.463Z" how="h-g-i-g-o"><point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/><detail><takv device="ASUS P027" platform="ATAK-CIV" os="24" version="4.0.0.7 (7939f102).1592931989-CIV"/><contact endpoint="*:-1:stcp" callsign="Bogon-1"/><uid Droid="Bogon-1"/><__group name="Dark Green" role="Team Member"/><status battery="100"/><track speed="0.0" course="74.30885078798654"/></detail></event>'
    #print(cotdata)
    sentdata=""
    try:
        sentdata = mysock.send(cotdata)
        #print("sent")
    except:
        print("push_tcp: Send data failed")
        return 0
    try:
        mysock.settimeout(1)
        rcvdata = mysock.recv(2048)
        #print("pushTCP Rcv Data:" + str(rcvdata))
    except:
        print("push_tcp: Rcv data failed")
        return 0
        
    time.sleep(sleeptime) # was 0.2 
    return sentdata
    

def callback(packet):
    global aprs_reports
    global aprs_reportsmax
    global lastcycle
    global sock

    #print(packet)
    try: 
        aprs_atoms = aprslib.parse(packet)
        if (aprs_atoms["format"] == "beacon"):
            #print("beacon skipped:" + str(packet))
            pass # Skip the rest

        else:    
            #print(aprs_atoms)
            aprs_source = aprs_atoms["from"]
            try:
                aprs_lat = str(round(aprs_atoms["latitude"],5))
                aprs_lon = str(round(aprs_atoms["longitude"],5))
            except:
                print(aprs_source + " No Lat/Lon")
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
            #print(aprs_source + " " + str(aprs_lat) + " " + str(aprs_lon) + " " + str(aprs_alt))
            if sleeptime > 0.1:
                print(aprs_source 
                    + " Lat:" + aprs_lat + " Lon:" + aprs_lon + " Alt:" + aprs_alt
                    #+ " Speed:" + aprs_speed + " Course:" + aprs_course 
                    + " Counter: " + str(aprs_reports)
                    )
            else:
                if int(aprs_reports % 10) == 0:
                    print("+", end="", flush=True)
                else:
                    #print(".", end="", flush=True)
                    pass
                    
            cot_xml = injectCoT.inject_cot(aprs_source, aprs_lat, aprs_lon, aprs_alt)
            #print("cot_xml is:" + str(cot_xml))
            sent = pushTCP(sock,cot_xml)
            if sent == 0:
                print("Push TCP failed- sent was zero")
                # force socket reopen
                aprs_reports = 9999999
            
            if aprs_reports >= aprs_reportsmax:
                #print("aprs_reports:" + str(aprs_reports))
                cycletime = int(time.time() - lastcycle)
                lastcycle = time.time()
                print()
                print( "Close and Reopen the TAK connection " + str(aprs_reports) + " reports "
                    + time.strftime("%d/%m/%y %H:%M:%S ", time.gmtime()))
                #print( "Close and Reopen the TAK connection " )
                #print( str(aprs_reportsmax / cycletime ) + " Reports / sec")
                print( str(round(aprs_reportsmax / cycletime, 2 )) + " Reports / sec")
                closeTCP(sock) 
                #print( "FTS server socket closed")
                print("Reopen the socket")
                sock = 0
                while sock == 0:
                    print( "Trying to reopen FTS server socket")
                    sock = openTCP(ATAK_IP, ATAK_PORT)
                    if sock == 0:
                        print("reopen failed")
                        time.sleep(57)
                print( "FTS server socket reopened")
                # Do a fake connect string
                #cot_xml =  b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<event version="2.0" uid="Bogon-H5NPCV052844VSE" type="a-f-G-E-V-C" time="2020-07-15T13:53:32.463Z" start="2020-07-15T13:53:32.463Z" stale="2020-07-15T13:59:47.463Z" how="h-g-i-g-o"><point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/><detail><takv device="ASUS P027" platform="ATAK-CIV" os="24" version="4.0.0.7 (7939f102).1592931989-CIV"/><contact endpoint="*:-1:stcp" callsign="Bogon-1"/><uid Droid="Bogon-1"/><__group name="Dark Green" role="Team Member"/><status battery="100"/><track speed="0.0" course="74.30885078798654"/></detail></event>'
                cot_xml =  connect_xml
                pushTCP(sock,cot_xml)
                aprs_reports = 0
            aprs_reports += 1
                
            #print("tcp sent")
            #input()


    except (aprslib.ParseError, aprslib.UnknownFormat) as exp:
        #print("parse failed:" + str(packet))
        pass

    except:
        #print("parse failed other error:" + str(packet))
        pass
#-----------------------------------------------------------------------------------------
# Main Program

# Setup a UID
my_uid = str(socket.getfqdn())
my_uid = my_uid + "-" + str(uuid.uuid1())
my_uid = bytes("APRS_inject-" + my_uid,"UTF-8")
print(my_uid)

# Setup a callsign for the main process
my_callsign = bytes("APRS-", "UTF-8") + my_uid[-6:]
print(my_callsign)

# get a time, does not really matter
xml_time = bytes(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"UTF-8")

# XML strings for the healthcheck
connect_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<event version="2.0" uid="' + my_uid + b'" type="t-x-c-t" time="' + xml_time + b'" start="' + xml_time + b'" stale="'+ xml_time + b'" how="h-g-i-g-o"><point lat="0.0" lon="0.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/><detail><takv platform="APRS_inject" os="24" version="1.0.0.0"/><contact endpoint="*:-1:stcp" callsign="' + my_callsign + b'"/><__group name="Dark Green" role="Team Member"/></detail></event>'
print(connect_xml)

# Now open the socket the ATAK Server
sock = 0
while sock == 0:
    print("Opening TAK Server")
    sock = openTCP(ATAK_IP, ATAK_PORT)
    # Sleep for a bit if the open failed
    if sock == 0:
        time.sleep(57)
    

# Send a connect string
cot_xml = connect_xml
pushTCP(sock,cot_xml)
print("Opened TAK Server" + str(sock))
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
    except:
        print("APRS consumer failed")

        # Sleep for a bit if failed
        time.sleep(11)
