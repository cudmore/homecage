# Robert H Cudmore
# 20180525

import os, subprocess
import platform, socket
from collections import OrderedDict
from datetime import datetime

def getSystemInfo():
	ret = OrderedDict()
	
	now = datetime.now()
	ret['date'] = now.strftime('%Y-%m-%d')
	ret['time'] = now.strftime('%H:%M:%S')

	ret['ip'] = whatismyip()
	ret['hostname'] = socket.gethostname()
	
	ret['cpuTemperature'] = cpuTemperature()
	
	ret['gbRemaining'], ret['gbSize'] = drivespaceremaining()
	
	ret['raspberryModel'] = raspberrymodel()
	ret['debianVersion'] = debianversion()
	
	return ret
	
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

def cpuTemperature():
	#cpu temperature
	res = os.popen('vcgencmd measure_temp').readline()
	cpuTemperature = res.replace("temp=","").replace("'C\n","")
	return cpuTemperature
	
def drivespaceremaining():
	#see: http://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
	statvfs = os.statvfs('/home/pi/video')
	
	#http://www.stealthcopter.com/blog/2009/09/python-diskspace/
	capacity = statvfs.f_bsize * statvfs.f_blocks
	available = statvfs.f_bsize * statvfs.f_bavail
	used = statvfs.f_bsize * (statvfs.f_blocks - statvfs.f_bavail) 
	#print 'drivespaceremaining()', used/1.073741824e9, available/1.073741824e9, capacity/1.073741824e9
	gbRemaining = available/1.073741824e9
	gbSize = capacity/1.073741824e9

	#round to 2 decimal places
	gbRemaining = "{0:.2f}".format(gbRemaining)
	gbSize = "{0:.2f}".format(gbSize)

	return gbRemaining, gbSize
	
def raspberrymodel():
	# get the raspberry pi version, we can run on version 2/3, on model B streaming does not work
	cmd = 'cat /proc/device-tree/model'
	child = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
	out, err = child.communicate() # out is something like 'Raspberry Pi 2 Model B Rev 1.1'
	out = out.decode('utf-8')
	return out

def debianversion():
	# get the version of Raspian, we want to be running on Jessie or Stretch
	dist = platform.dist() # 8 is jessie, 9 is stretch
	ret = ''
	if len(dist)==3:
		ret = dist[0] + ' ' + dist[1]
		'''
		if float(dist[1]) >= 8:
			#logger.info('Running on Jessie, Stretch or newer')
		else:
			#logger.warning('Not designed to work on Raspbian before Jessie')
		'''
	else:
		pass
	return ret