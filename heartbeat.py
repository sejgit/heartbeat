#!/usr/bin/env python3
"""
heartbeat to isy for pi's

ChangeLog
2017 06 02 sej init from fishtank.py
2019 10 05 format-all
"""

# imports and parse args

# imports
import datetime as dt
import time
import logging
import logging.handlers
import os
import sys
import argparse
import paul
import requests

# parsing
parser = argparse.ArgumentParser(description="Heartbeat to ISY")
parser.add_argument("-t",
                    "--test",
                    action="store_true",
                    help="for offline testing")
parser.add_argument("-n", "--name", help="name label for output like prowl")
parser.add_argument("-d", "--dir", help="home directory")
parser.add_argument("-i",
                    "--isy",
                    default=0,
                    type=int,
                    help="isy state var number for ISY heartbeat")
args = parser.parse_args()

if args.isy:
    print("\n output to ISY state var:" + str(args.isy))

userdir = os.path.expanduser("~")
if args.dir:
    dir = os.path.join(args.dir, "")
else:
    dir = userdir + "/heartbeat/"

if os.path.isdir(dir):
    print("\n" + dir + "   ***using directory***\n")
else:
    print("\n" + dir + "   ***not a dir***\n")

if args.name:
    heartlabel = args.name
else:
    heartlabel = "Heartbeat"

#
# get logging going
#

# set up a specific logger with desired output level
LOG_FILENAME = "heartbeat.log"

logger = logging.getLogger("HeartbeatLogger")

# add the rotating log message handler
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME,
                                          maxBytes=100000,
                                          backupCount=5)
if args.test:
    logger.setLevel(logging.DEBUG)
    fh.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
    fh.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter(fmt="%(asctime)s %(levelname)s %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)

#
# variables
#

# prowl vars
try:
    p = paul.Paul()

    apikey1 = ""
    with open(os.path.join(userdir, ".ssh/.paul1"), "r") as f:
        apikey1 = f.read()
        apikey1 = apikey1.strip()

except IOError:
    logger.error("Could not read prowl api file")
    exit()

# ISY vars
try:
    isyip = ""  # use http://10.0.1.x format
    isylogin = ""
    isypass = ""
    with open(os.path.join(userdir, ".ssh/isy.auth"), "r") as f:
        isyip = f.readline()
        isyip = isyip.rstrip()
        isylogin = f.readline()
        isylogin = isylogin.rstrip()
        isypass = f.readline()
        isypass = isypass.rstrip()
        logger.info("ISY IP = '" + isyip + "'")

except IOError:
    logger.error("Could not read ISY auth file")
    exit()

#
# defined functions
#


def prowl(event, description, pri=None):
    """Function to send EVENT, DESCRIPTION, and (PRI)ORITY to Prowl service

           p.push(apikey,
                   args.name,
                   args.event,
                   args.description,
                   url=args.url,
                   priority=args.priority)
    """
    try:
        p = paul.Paul()

        # prowl push to sej
        p.push(apikey1, heartlabel, event, description, url=None, priority=pri)
        success = True
    except IOError:
        logger.error("prowl error")
        success = False
    return success


def heartbeat(ast):
    """Heartbeat function passing status AST."""
    if ast == " ":
        ast = "*"
        s = isyip + "/rest/vars/set/2/" + str(args.isy) + "/1"
    else:
        ast = " "
        s = isyip + "/rest/vars/set/2/" + str(args.isy) + "/0"

    try:  # heartbeat
        if args.test:
            logger.info("isy heartbeat = " + ast)
        r = requests.get(s, auth=(isylogin, isypass))
        if r.status_code != requests.codes.ok:
            logger.error("isy heartbeat error =" + str(r.status_code))
            prowl("heartbeat", "no ISY communications", 0)
    except Exception:
        logger.error("isy heartbeat exception")
    return ast


#
# first run items
#

#
# main loop
#


def main():
    timestamp = dt.datetime.now().time()
    logger.info("nowtime = " + str(timestamp)[:5])

    # log & push temp on first run
    hb = "*"
    hb = heartbeat(hb)

    while True:
        try:
            time.sleep(60)  # wait one minute
            hb = heartbeat(hb)

            # start or stop light/bubbles
            timestamp = dt.datetime.now().time()
            if args.test:
                logger.info("nowtime = %s", str(timestamp)[:5])

        except KeyboardInterrupt:
            print("\n\nKeyboard exception. Exiting.\n")
            logger.info("keyboard exception")
            sys.exit()

        except Exception:  # pylint: disable=broad-except
            logger.info("program end: %s", sys.exc_info()[0])
            sys.exit()
    return


if __name__ == "__main__":
    main()
    sys.exit()
