import os
import time
import CoT
import random

# Setup ATAK Server Params
#ATAK_IP = os.getenv('ATAK_IP', '204.48.30.216')
#ATAK_PORT = int(os.getenv('ATAK_PORT', '8087'))

ATAK_IP = os.getenv('ATAK_IP', '172.16.10.30')
ATAK_PORT = int(os.getenv('ATAK_PORT', '48099'))


#ATAK_IP = os.getenv('ATAK_IP', '127.0.0.1')

ATAK_PROTO = os.getenv('ATAK_PROTO', 'TCP')
#ATAK_PROTO = os.getenv('ATAK_PROTO', 'UDP')


# send the CoT to the server
def inject_cot(target_id, target_lat, target_lon, target_alt):
    # Setup Param Tuple for CoT
    params = {  # working KM4BA 
        "lat": target_lat,
        "lon": target_lon,
        "hae": target_alt,
        "uid": target_id,
        "platform": "injector",
        "identity": "friend",
        "dimension": "land-unit",
        "entity": "civilian",
        #"type": "G-U-C"
        #"type": "U-C-A-W",
        "type": "E-V-C",
    }

    #print ("Params:\n" + str(params))
    
    cot = CoT.CursorOnTarget()
    try:    
        cot_xml = cot.atoms(params)
    except:
        print("CoT.atoms failed")
        exit()

    #cot_xml ='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><event version="2.0" uid="ANDROID-R58KB1ALPEL" type="a-f-G-U-C" time="2020-07-07T12:39:18.275Z" start="2020-07-07T12:39:18.275Z" stale="2020-07-07T12:45:33.275Z" how="h-g-i-g-o"><point lat="33.0" lon="-84.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/><detail><takv os="29" version="4.0.0.7 (7939f102).1592931989-CIV" device="SAMSUNG SM-G960U" platform="ATAK-CIV"/><contact endpoint="*:-1:stcp" callsign="Pinzgauer"/><uid Droid="Pinzgauer"/><__group role="Team Member" name="Dark Green"/><status battery="92"/><track course="74.47431804837191" speed="0.0"/></detail></event>\n'

    #cotxml='<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<event version="2.0" uid="bogonuid" type="a-f-G-U-C" time="2020-07-07T12:39:18.275Z" start="2020-07-07T12:39:18.275Z" stale="2020-07-07T12:45:33.275Z" how="h-g-i-g-o"><point lat="33.0" lon="-84.0" hae="9999999.0" ce="9999999.0" le="9999999.0"/><detail><takv  os="99" version="1.0.0" device="nonya" platform="Injector"/><contact endpoint="*:-1:stcp" callsign="bogon-callsign"/><uid Droid="bogon-droid-uid"/><__group role="" name="" /></detail></event>'
       
    #cot_xml = cot_xml + "\n"

    #cot_xml = bytes(cot_xml,"UTF-8")
    
    #print ("XML message:")
    #print (cot_xml)
    
    #print ("\nPushing to ATAK...")
    #if ATAK_PROTO == "TCP":
      #sent = cot.pushTCP(ATAK_IP, ATAK_PORT, cot_xml)
      #sock = cot.openTCP(ATAK_IP, ATAK_PORT)
      #print("Sending:")
      #input("Press Enter")
      #sent = cot.pushTCP(sock, cot_xml)
      ##print("pushed")
      ##input("Press Enter")
      #closestatus = cot.closeTCP(sock)
      #time.sleep(0.2)
      #return sent
    #else:
      #sent = cot.pushUDP(ATAK_IP, ATAK_PORT, cot_xml)
    #print (str(sent) + " bytes sent to " + ATAK_IP + " on port " + str(ATAK_PORT))
    return cot_xml

#print ("inject_CoT loaded")
