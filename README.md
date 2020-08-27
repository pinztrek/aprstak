# aprstak

## Reads APRS Position reports and injects into TAK servers

## Motivation
This program is the first step of integrating the APRS world with TAK and specifically ATAK. Goals:
* Utilize existing APRS tools and infrastructure (APRS.IS, aprslib, etc)
* Allow update of ATAK user positions (PLIs) based on APRS and similar (HF ALE) amateur radio based reports
* (Long term) Allow APRS generated messages to be sent to stations also on ATAK
* (Long term) Allow the use of APRS radio connection to feed in/out of local ATAK users. IE: use APRS for transport for a narrow subset of TAK CoT's. (PLI and GeoChat)


## Build status
The aprstak code is in ugly but functioning state, but continues to evolve/improve. 
### What works:
* Injection of APRS position reports from APRS.IS into TAK server using TAK standard CoT XML
* Selection of 2 public TAK servers, a local (same IP) server, or a hardcoded IP/port
* Selection of US regional zones, a hardcoded Lat/Long, and optional radius for LL based reports
* Multiple debugging levels
* systemd service to run the program
* logrotate config file to rotate the logs

### What's next:
* extension of takpak.takcot() to return commonly used params from a received CoT
* establishment of a "last heard" TAK user/callsign queue with key params (callsign, UID, team). This will be seeded by user.json. 
* ongoing read/parse of CoT's between aprs sending events. Or a threaded approach. This is critical to maintaining the user list.
* parsing of APRS messages and sending as GeoChat to matching users online in TAK
* Potential initiation of outbound APRS message if a GeoChat to a whitelisted user is detected from the server

## Features
Currently aprstak just injects APRS position reports into a TAK server:
* Stations which match an online ATAK user callsign will update the position of that user. 
    * This is dummied out now with a static user file to correlate callsigns and UID's. 
    * The users.json file can be generated using the read_cot.py demo code in the takpak library.
    * Ultimately aprstak will track and add users on the fly so that if a new user callsign shows up it will be checked for match.
* Stations which are not active users are shown using an icon, and are not listed as active users when the CoT is displayed in ATAK


## Prerequisites
* python 3.x. In fact, the libraries and code will give very non-intuitive "almost working" behavior sometimes under older pythons. Main development was on 3.8.
* takpak https://github.com/pinztrek/takpak
* aprslib https://github.com/rossengeorgiev/aprs-python

## Installation
No specific installation is required once takpak & aprslib is installed on the system you plan to execute the code from. 

* pip3 install https://github.com/pinztrek/takpak/archive/master.zip  (until it's released as a package)
* pip3 install aprslib

You do need to set the APRS.IS user ID and password:

* APRS Login info, -1 for password means read only

aprs_user = "MYCALL-TS"

aprs_password = "-1"

## How to use
Typical run string would be:

### Run on local system, info level logging, NE US zone
python3 aprstak.py -l --logging=info --neus

### Run on FTS Public instance, warning level logging, NW US zone
python3 aprstak.py -f --logging=warning --nwus

### Run on Discord Public server, debug level logging, SE US zone, reconnect TAK every 100 CoTs sent
python3 aprstak.py -d --logging=debug --seus --max=100

### Run on hardcoded server IP, centered around a hardcoded Lat/Long, with a 100 mile range
python3 aprstak.py -h --range=100

### Ask for the server, warning level logging (default), SE US zone (default), reconnect TAK every 10,000 CoTs sent (default), set the user directory to check for users.json
python3 aprstak.py --userdir="/home/myuser/aprstak"

## Contribute

If you want to contribute please direct message/email me. I'll need a real email address or github account name, along with a short description of the project you are using it for. 

## Collaboration Approach
Please do not commit to the master branch without discussion. Ideally, we probably need to use the "Fork and Pull Request" model. (See https://reflectoring.io/github-fork-and-pull/ if not familiar). This will allow us to use pull requests and review before committing changes to the master. Alternatively, at least create your own dev branch. But this (I think) makes it a bit harder to tell when edits are ready to be integrated. 

## Credits
While aprstak and takpak is original code, it would not be possible some of the APRS libraries and documentation for sites like APRS.IS.   

* APRSLib 

https://github.com/rossengeorgiev/aprs-python
https://aprs-python.readthedocs.io/en/latest/


## License
This code is licensed under GPL3. Please note this means that any derivative code would need to be also released under the same license. 

GPL3 © Alan Barrow
