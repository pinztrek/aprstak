import datetime as dt
import uuid
import xml.etree.ElementTree as ET
import socket
import logging
import time

logger = logging.getLogger("django")


ID = {
    "pending": "p",
    "unknown": "u",
    "assumed-friend": "a",
    "friend": "f",
    "neutral": "n",
    "suspect": "s",
    "hostile": "h",
    "joker": "j",
    "faker": "f",
    "none": "o",
    "other": "x"
}
DIM = {
    "space": "P",
    "air": "A",
    "land-unit": "G",
    "land-equipment": "G",
    "land-installation": "G",
    "sea-surface": "S",
    "sea-subsurface": "U",
    "subsurface": "U",
    "other": "X"
}

DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

class CursorOnTarget:


    def atoms(__self, unit):
        timer = dt.datetime
        now = timer.utcnow()
        zulu = now.strftime(DATETIME_FMT)
        #stale_part = now.minute + 15
        # for APRS stale it out 5 minutes later
        stale_now=now + dt.timedelta(hours=0, minutes=10)
        #stale_hr = now.hour
        #if stale_part > 59:
        #    stale_part = stale_part - 60
            # Need to also check for hour rollover. Just add seconds to timer instead?
        #    stale_hr = now.hour +1
        #stale_now = now.replace(minute=stale_part)
        #stale_now = stale_now.replace(hour=stale_hr)
        stale = stale_now.strftime(DATETIME_FMT)

        unit_id = ID[unit["identity"]] or ID["none"]
    
        cot_type = "a-" + unit_id + "-" + DIM[unit["dimension"]]

        if "type" in unit:
          cot_type = cot_type + "-" + unit["type"]

        if "uid" in unit:
          cot_id = unit["uid"]
        else:
          cot_id = uuid.uuid4().get_hex()

        evt_attr = {
            "version": "1.0",
            "uid": cot_id,
            "time": zulu,
            "start": zulu,
            "stale": stale,
            #"how": "h-e",
            "how": "m-g", 
            "type": cot_type
        }

        pt_attr = {
            "lat": str(unit["lat"]),
            "lon":  str(unit["lon"]),
            #"hae": "0",   #unit["hae"],
            "hae": str(unit["hae"]),
            "ce": "10",
            "le": "10"
            #,"remarks": "APRS-Inject"
        }

        contact_attr = {
            "endpoint": "*:-1:stcp",
            "callsign": cot_id
        }

        precision_attr = {
            "altsrc": "GPS",
            "geopointsrc": "GPS",
        }

        group_attr = {
            "role": "Team Member",
            #"name": "Dark Green"
            "name": "Purple"
            #"name": "APRS"
        }

        platform_attr = {
            "OS": "29",
            "platform": 'APRS-COT',
            "version": "1.0.0"
        }

        color_attr = {
            "argb": '-8454017'
            #"argb": '0'
            #"argb": '255'
        }

        icon_attr = {
            #"iconsetpath": '34ae1613-9645-4222-a9d2-e5f243dea2865/Military/soldier6.png'
            #"iconsetpath": '34ae1613-9645-4222-a9d2-e5f243dea2865/Military/soldier6.png'
            "iconsetpath": 'f7f71666-8b28-4b57-9fbb-e38e61d33b79/Google/placemark_circle.png'
        }
        remarks_attr = {
            "source": "APRS-Inject",
            "keywords": "APRS,KM4BA"
        }
    
        cot = ET.Element('event', attrib=evt_attr)
        ET.SubElement(cot,'point', attrib=pt_attr)
        #ET.SubElement(cot, 'detail')
        # Create Detail element, save the handle
        #detail = ET.SubElement(cot, 'detail', attrib=detail_attr)
        detail = ET.SubElement(cot, 'detail')
        # Now add some subelements to detail
        #ET.SubElement(detail,'contact', attrib=contact_attr)
        ET.SubElement(detail,'precisionlocation', attrib=precision_attr)
        #ET.SubElement(detail,'__group', attrib=group_attr)
        ET.SubElement(detail,'takv', attrib=platform_attr)
        #ET.SubElement(detail,'color', attrib=color_attr)
        ET.SubElement(detail,'usericon', attrib=icon_attr)
        ET.SubElement(detail,'remarks', attrib=remarks_attr)

    
        #cot_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + b'\n' + ET.tostring(cot) + b'\n'
        cot_xml = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + b'\n' + ET.tostring(cot)
        #cot_xml = ET.tostring(cot)
        #print(cot_xml)
        return cot_xml

    def pushUDP(__self, ip_address, port, cot_xml):
        sent = sock.sendto(cot_xml, (ip_address, port))
        return sent

    def openTCP(__self, ip_address, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn = sock.connect((ip_address, port))
        except:
            print("Cannot connect to " + str(ip_address) + ":" + str(port))
            exit()
        #sentdata = sock.send(b'\n')
        #rcvdata = sock.recv(1024)
        return sock

    def closeTCP(__self, sock):
        closereturn = sock.shutdown(1)
        time.sleep(0.5)
        closereturn = sock.close()
        return closereturn

    def pushTCP(__self, sock, cot_xml):
        sentdata = sock.send(cot_xml)
        rcvdata = sock.recv(1024)
        #print("pushTCP Rcv Data:" + str(rcvdata))
        #time.sleep(0.1)
        return sentdata

    def pushTCPold(__self, ip_address, port, cot_xml):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_address, port))
            time.sleep(0.9)
            #s.sendall(bytes('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n',"UTF-8")+b'\n')
            #time.sleep(0.2)
            sent = s.sendall(cot_xml)
            #data = s.recv(1024)
            #print('Received1', repr(data))
            data = ''
            #data = s.recv(1024)
            #print('Received2', repr(data))
            
            time.sleep(0.5)
            s.shutdown(1)
            time.sleep(0.5)
            s.close()
            return sent



        return sentdata
