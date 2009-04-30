"""
Timber Log Watcher v1.0 by ewall 2009-03-17
(c)2009 Eric W. Wallace/Atlantic Fund Administation

Description: Tails a log file and sends alert emails when the watched terms are seen.

Usage: Configure Timber.ini with the global options and words you want to watch for.
"""

__author__ = "Eric W. Wallace <e@ewall.org>"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2009/03/17 $"
__copyright__ = "Copyright (c)2009 Eric W. Wallace & Atlantic Fund Administration"
__license__ = "Creative Commons Attribution-ShareAlike (http://creativecommons.org/licenses/by-sa/3.0/)"

#from datetime import datetime
from datetime import datetime
from string import Template
import ConfigParser
import sys, os.path
import time, re

### Constants
VERBOSE = True
configFileName = 'Timber.ini'

stringSubstitutions = dict({
    'YEAR'        : datetime.now().strftime('%Y'),
    'YEARSHORT'   : datetime.now().strftime('%y'),
    'MONTH'       : datetime.now().strftime('%m') if datetime.now().strftime('%m')[:1] != '0' else datetime.now().strftime('%m')[1:],
    'MONTHPAD'    : datetime.now().strftime('%m'),
    'MONTHABBREV' : datetime.now().strftime('%b'),
    'MONTHNAME'   : datetime.now().strftime('%B'),
    'DAY'         : datetime.now().strftime('%d') if datetime.now().strftime('%d')[:1] != '0' else datetime.now().strftime('%d')[1:],
    'DAYPAD'      : datetime.now().strftime('%d'),
    'DAYABREV'    : datetime.now().strftime('%a'),
    'DAYNAME'     : datetime.now().strftime('%A') })

### Functions

def sendmail(hostname=None, sender='', to='', subject='', text=''):
    """ simple sendmail relay using built-in modules """
    import email.Message, email.iterators, email.generator
    import smtplib

    message = email.Message.Message()
    message["To"] = to
    message["From"] = sender
    message["Subject"] = subject
    message.set_payload(text)
    mailServer = smtplib.SMTP(hostname)
    smtpresult = mailServer.sendmail(sender, to, message.as_string())
    mailServer.quit()
    if smtpresult:
        errstr = ""
        for recip in smtpresult.keys():
            errstr = "Could not deliver mail to: %s\nServer said: %s\n%s\n%s" % (recip, smtpresult[recip][0], smtpresult[recip][1], errstr)
        raise smtplib.SMTPException, errstr
    else:
        if VERBOSE: print "Email sent."

### Main
if __name__ == '__main__':

    # Redirect output
    sys.stdout = open('Timber.log', 'wa')
    sys.stderr = open('Timber_errors.log', 'wa')

    # Read global options from config file
    config = ConfigParser.RawConfigParser()
    config.read(configFileName)
    MAILSERVER = config.get('options', 'mailserver')
    FROMEMAIL = config.get('options', 'fromemail')
    REPORTEMAIL = config.get('options', 'reportemail')
    MESSAGES = dict(config.items("messages")) #keyword pairs for error levels and messages to send
    WATCHES = dict(config.items("watches")) #keyword pairs for terms to watch and error levels

    # Date substitutions in FILENAME
    FILENAME = config.get('options', 'filename')
    t = Template(FILENAME)
    FILENAME = t.safe_substitute(stringSubstitutions)

    # Double-check options
    if not (os.path.exists(FILENAME)):
        print "\nERROR: file '" + FILENAME + "' not found!\n"
        sys.exit(2)
    if MESSAGES=={} or WATCHES=={}:
        print "\nERROR: config file '" + configFileName + "' is incomplete!\n"
        sys.exit(3)

    # Open the logfile
    try:
        watchFile = open(FILENAME, "rb")
    except IOError:
        print "\nERROR: can't open '" + FILENAME + "'!\n"
        sys.exit(2)

    # Loop forever unless the user types Ctrl-c
    try:
        while True:
            where = watchFile.tell()
            line = watchFile.readline()
            # nothing new, so wait a bit
            if not line:
                time.sleep(3)
                watchFile.seek(where)
            # now the interesting stuff happens
            else:
                for watchFor in WATCHES.keys():
                    found = None
                    
                    # is our watch pattern a regex?
                    if watchFor.startswith("/") and watchFor.endswith("/"):
                        # convert pattern into a raw string and remove the magic /'s
                        found = re.search(r"%s" % watchFor[1:-1], line)
                    # non-regex
                    else:
                        # look for the word anywhere in the line
                        found = re.search(watchFor, line, re.IGNORECASE)

                    # send the alert if we found one                
                    if found:
                        errorLevel = WATCHES[watchFor]
                        subject = MESSAGES[errorLevel]
                        message = subject + "\n"
                        message += "Log watcher found the word '" + found.group() + "'\n"
                        message += "in the log file '" + FILENAME + "'\n"
                        message += "at " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + "\n"
                        message += "Please investigate!\n"
                        sendmail(MAILSERVER, FROMEMAIL, REPORTEMAIL, subject, message)

    except KeyboardInterrupt:
        watchFile.close()
        sys.exit(0)
