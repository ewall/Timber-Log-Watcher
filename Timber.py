"""
Timber Log Watcher v1.0.2 by ewall 2009-05-12
(c)2009 Eric W. Wallace/Atlantic Fund Administation

Description: Tails a log file and sends alert emails when the watched terms are seen.

Usage: Configure Timber.ini with the global options and words you want to watch for.
"""

__author__ = "Eric W. Wallace <e@ewall.org>"
__version__ = "$Revision: 1.0.1 $"
__date__ = "$Date: 2009/05/07 $"
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
SLEEPSECONDS = 10 #how long to wait for new writes to the target file
WAITSECONDS = 300 #how long to wait before retrying the file load
MAXWAIT = 21600 # = 6 hrs
configFileName = 'Timber.ini'

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

def getFilename(configParser):
	""" fetches target filename from config and performs date substitutions """
	#we want these to be "fresh" every time the function is run
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
	myFilename = configParser.get('options', 'filename')
	t = Template(myFilename)
	return t.safe_substitute(stringSubstitutions)

def getFileHandle(filename):
	""" get file handle, returns None when it's not there """
	try:
		myFile = open(filename, "rb")
	except IOError:
		return None
	return myFile

def getWatchFile():
	""" loads global file handle, waits or fails as appropriate """
	global watchFile, where #yeah, yeah, I know this is bad form!
	watchFile = getFileHandle(FILENAME)
	if WAITFORFILE == True:
		waited = 0
		while watchFile == None:
			if waited >= MAXWAIT:
				#too many retries, notify and quit
				subject = "Timber Log Watcher exiting"
				message = "Target file not found; maximum wait period reached. Program is exiting."
				sendmail(MAILSERVER, FROMEMAIL, REPORTEMAIL, subject, message)
				print "\nERROR: reached maximum limit while waiting for file.\n"
				sys.exit(2)
			if VERBOSE: print "File not ready; sleeping..."
			time.sleep(WAITSECONDS)
			waited += WAITSECONDS
			watchFile = getFileHandle(FILENAME)
	else:
		if watchFile == None:
			#die if we aren't supposed to wait and the file is not there
			print "\nERROR: can't open '" + FILENAME + "'!\n"
			sys.exit(2)
        where = 0 #reset cursor to head of file

### Main
if __name__ == '__main__':

	# Redirect output
	logFile = open('Timber.log', 'wa', 0) #unbuffered
	sys.stdout = sys.stderr = logFile

	# Read global options from config file
	config = ConfigParser.RawConfigParser()
	config.read(configFileName)
	FILENAME = getFilename(config)
	wait = config.get('options', 'waitforfile')
	if wait == "1" or wait.lower() == "true":
                WAITFORFILE = True
        else:
                WAITFORFILE = False
	MAILSERVER = config.get('options', 'mailserver')
	FROMEMAIL = config.get('options', 'fromemail')
	REPORTEMAIL = config.get('options', 'reportemail')
	MESSAGES = dict(config.items("messages")) #keyword pairs for error levels and messages to send
	WATCHES = dict(config.items("watches")) #keyword pairs for terms to watch and error levels

	# Double-check options
	if MESSAGES=={} or WATCHES=={}:
		print "\nERROR: config file '" + configFileName + "' is incomplete!\n"
		sys.exit(3)

	# Variable prep
	lastDate = datetime.now().strftime('%d')
	getWatchFile() #loads watchFile handle

	# Loop forever (unless the user types Ctrl-c)
	while True:
		try:
			where = watchFile.tell()
			line = watchFile.readline()

			# nothing new, so wait a bit
			if not line:
				time.sleep(SLEEPSECONDS)

				if lastDate != datetime.now().strftime('%d'):
					if VERBOSE: print "Date has changed, reloading target file."
					getWatchFile()
				lastDate = datetime.now().strftime('%d')
				
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
						if VERBOSE: print "Log watcher found the term '" + found.group() + "'."

						errorLevel = WATCHES[watchFor]
						subject = MESSAGES[errorLevel]
						message = subject + "\n"
						message += "Log watcher found the term '" + found.group() + "'\n"
						message += "in the log file '" + FILENAME + "'\n"
						message += "at " + time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) + "\n\n"
						
						#gather the next few log entries
						message += "Below are the recent lines from the log:\n\n"
						rollback = watchFile.tell() #store the cursor for rollback
						watchFile.seek(where) #replay the last line
						nextLine = watchFile.readline()
						while nextLine:
							message += nextLine
							nextLine = watchFile.readline()
							if nextLine.strip()=="": break #stop at blank lines
						watchFile.seek(rollback)
						
						#now send the email
						sendmail(MAILSERVER, FROMEMAIL, REPORTEMAIL, subject, message)

		except IOError:
			print "\nERROR: IOError while processing, exiting now.\n"
			logFile.close()
			watchFile.close()
			sys.exit(2)
	
		except KeyboardInterrupt:
			print "\nUser stopped program with CTRL-c, exiting now.\n"
			logFile.close()
			watchFile.close()
			sys.exit(0)
