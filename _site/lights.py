import os #for interrupt
import time, datetime
import home
from random import randrange #for testing

tempInterval = 3*60 # 1*60 #2*60 == 2 minutes
lasttime = -tempInterval

numEventsToPurge = 200 #ammass this number of events and then purge

h=home.home()
h.logfile_new()

#testing
testinterval = 5 #seconds
lasttest = -testinterval
logNumber = 0

def cleanup():
	print '\n'
	print '-->> turning ir and white lights off'
	h.ir(0)
	h.white(0)
	print '-->> closing log file'
	#h.logfile_close()
	print '-->> testhome.py is done.'

while True:
	try:
		now = time.time()
		elapsed = now - lasttime
	
		#testing
		if (now - lasttest) > testinterval:
			lasttest = now
			ts = h.timestamp()
			#h.logfile_write(ts, 'test1', randrange(0,5), randrange(10,20))

		#check hour and adjust lights (will log to file)
		hour = datetime.datetime.fromtimestamp(now).hour
		turnOnIR = (hour >= 18 or hour < 6) and (h.ir()==0)
		turnOnWhite = hour>=6 and hour<18 and (h.white()==0)
		#swapped
		#turnOnWhite = (hour >= 18 or hour < 6) and (h.ir()==0)
		#turnOnIR = hour>=6 and hour<18 and (h.white()==0)
		if turnOnWhite:
			h.white(1)
			h.ir(0)
			h.logfile_write(ts, 'whitelight', 1, 0)
			h.logfile_write(ts, 'irlight', 0, 1)
		elif turnOnIR:
			h.ir(1)
			h.white(0)
			h.logfile_write(ts, 'whitelight', 0, 0)
			h.logfile_write(ts, 'irlight', 1, 0)

		if (elapsed > tempInterval):
			lasttime = now		
			try:
				ts = h.timestamp()
				(temp, hum) = h.temperature()
				#if temp and hum: #don't log errors
				#print ts, 'tandh is:', temp, hum
				h.logfile_write(ts, 'tandh', temp, hum)
			except:
				raise

		#h.log['a'] is added to with h.logfile_write()
		'''
		numEvents = len(h.log['a'])
		if numEvents > numEventsToPurge:
			h.push_sql_log(logNumber)
			logNumber += 1
		'''
		
		time.sleep(0.005)

	except KeyboardInterrupt:
		cleanup()
		raise

cleanup()


