import sched, time, os, psutil, sys
from datetime import datetime

# Script which will check if it get's ping response from one or
# several external ip's. After X amount of fails, it will execute
# a command. Perfect for i.e. headless Raspberry PIs which you want
# to either reboot or shutdown if it looses connection.

# More checkpoints can be added simply by adding more s.enter at the end
logfile = False # Set to False if not to log, add filepath to log
printmode = True # Set to False if silent mode in console
localips = ['10.0.0.138']
externalips = ['8.8.8.8', '1.1.1.1']
localinterval = 1*60 # seconds between each check
externalinterval = 2*60 # seconds between each check
localfails = 2 # how many fails before doing something
externalfails = 2 # how many fails before doing something
localresult = 'init 6' # what to do if failing
externalresult = 'init 0' # what to do if failing

# Do not touch the following variables
externalcount = 0
internalcount = 0
timers = {}

def check_if_running(script):
    for q in psutil.process_iter():
        match1 = False
        match2 = False
        match3 = False
        for r in q.cmdline():
            if "python" in r:
                match1 = True
            if script in r:
                match2 = True
            if q.pid !=os.getpid():
                match3 = True
        if match1 == True and match2 == True and match3 == True:
            return True
    return False

def check_ping(iplist, type):
    status = False
    for ip in iplist:
        response = os.system("ping -c 1 " + ip + "> /dev/null")
        # and then check the response...
        if response == 0:
            status = True
            logger("Pinging %s returned True" % ip, type)
            break
        else:
            logger("Pinging %s returned False" % ip, type)
            status = False

    return status

def check_network(type, ips, interval, fails, result):
    global timers
    if type not in timers:
        timers[type] = 0
    if check_ping(ips, type) == False:
        timers[type] += 1
        if timers[type] >= fails:
            logger("%s fails of %s - doing something...." % (timers[type], fails), type)
            timers[type] = 0
            os.system(result)
            exit()
        else:
            logger("%s fails of %s - not doing anything yet..." % (timers[type], fails), type)
    else:
        logger("Success.. Resetting fail counter...", type)
        timers[type] = 0
    s.enter(interval, 1, check_network, argument=(type, ips, interval, fails, result))


def logger(input, type="GENERAL"):
    printtext = "[" + datetime.now().strftime("%H:%M:%S") + "][" + type + "] " + input
    if logfile is not False:
        with open(logfile, "a") as logfilewriter:
            logfilewriter.write(printtext + "\n")
    if printmode is True:
        print(printtext)

logger("Starting...")
logger("Checking if already running %s" % sys.argv[0])
if check_if_running(os.path.basename(sys.argv[0])) is True:
    logger("Already running, terminating...")
    exit()
else:
    logger("Not running.. Continuing...")
s = sched.scheduler(time.time, time.sleep)
logger("Initiating with interval: %sseconds, max fails: %s, result if failing: %s" % (localinterval, localfails, localresult), "LOCAL")
s.enter(localinterval, 2, check_network, argument=("LOCAL", localips, localinterval, localfails, localresult))
logger("Initiating with interval: %sseconds, max fails: %s, result if failing: %s" % (externalinterval, externalfails, externalresult), "EXTERNAL")
s.enter(externalinterval, 1, check_network, argument=("EXTERNAL", externalips, externalinterval, externalfails, externalresult))
s.run()