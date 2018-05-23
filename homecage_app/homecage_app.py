from __future__ import print_function	# (at top of module)

import os, sys, json
from datetime import datetime
from subprocess import check_output

#import mimetypes # to send files to ios

from flask import Flask, render_template, send_file, jsonify, abort, request#, redirect, make_response
from flask_cors import CORS

import logging
from logging.handlers import RotatingFileHandler
	
from home import home

print('__name__:', __name__)

#print('__name__:', __name__)
app = Flask('homecage')
#app = Flask(__name__)
CORS(app)

# turn off printing web request logs to console
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

logHandler = RotatingFileHandler('log.log', maxBytes=100000) #, backupCount=1)
logHandler.setLevel(logging.DEBUG)
myFormatter = logging.Formatter(
	"[%(asctime)s] {%(filename)s %(funcName)s:%(lineno)d} %(levelname)s - %(message)s")
logHandler.setFormatter(myFormatter)

# set the app logger level
app.logger.setLevel(logging.DEBUG)
#app.logger.setFormatter(myFormatter) # this does not work
app.logger.addHandler(logHandler)	

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.ERROR)
#logger.addHandler(logHandler)

# this works but I want error to be looged as well
# figure out how to use app.logger
'''
logger = logging.getLogger('homecage')
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler('log.log', maxBytes=20000) #, backupCount=10)
handler.setFormatter(myFormatter)
logger.addHandler(handler)
'''

'''
strmHandler = logging.StreamHandler(sys.stderr)
strmHandler.setFormatter(myFormatter)
logger.addHandler(strmHandler)
'''

#
home = home()


def getStatus():
	# Get struct of status from the backend
	status = home.getStatus()
	return status
	
@app.before_request
def myBeforeRequest():
	#print('before_request()')
	pass
	
@app.after_request
def myAfterRequest(response):
	#print('after_request()')
	if request.endpoint is None or request.endpoint in ["status", "lastimage"]:
		# ignore
		pass
	else:
		#request.endpoint is name of my function (not web address)
		#print(request.url)
		app.logger.debug('after ' + request.url)
	return response
	
@app.route('/')
def hello_world():
	app.logger.debug('/')
	return render_template('index.html')

@app.route('/log')
def log():
	return send_file('info.log')
	
@app.errorhandler(404)
def page_not_found(e):
	#return render_template('404.html'), 404
	return 'Error 404: File not found. This happens when you manually delete video files.'
	
# help
@app.route('/help')
def dispHelp():
	return render_template('help.html')

# state of server, queried about every second
@app.route('/status')
def status():	
	theStatus = getStatus()
	return jsonify(theStatus)
	
# params that can be set by the user
@app.route('/config')
def config():
	#print 'app.route config()'
	status = home.getConfig()
	return jsonify(status)
	
@app.route('/lastimage')
def lastimage():
	myImage = 'static/still.jpg'
	return send_file(myImage)
	
@app.route('/record/<int:onoff>')
def record(onoff):
	print('record() onoff:', onoff)
	home.record(onoff)

	status = getStatus()
	return jsonify(status)
	
@app.route('/stream/<int:onoff>')
def stream(onoff):
	print('stream() onoff:', onoff)
	home.stream(onoff)
	status = getStatus()
	return jsonify(status)
	
@app.route('/arm/<int:onoff>')
def arm(onoff):
	print('arm() onoff:', onoff)
	home.arm(onoff)
	status = getStatus()
	return jsonify(status)

@app.route('/simulate/triggerin')
def sim_triggerin():
	home.triggerIn_Callback(1)
	return jsonify(getStatus())
	
@app.route('/simulate/frame')
def sim_frame():
	home.frame_Callback(1)
	return jsonify(getStatus())

@app.route('/simulate/stop')
def sim_stop():
	home.stop()
	return jsonify(getStatus())
	
	
@app.route('/irLED/<int:onoff>')
def irLED(onoff):
	print('irLED() onoff:', onoff)
	home.irLED(True if onoff else False)
	status = getStatus()
	return jsonify(status)
	
@app.route('/whiteLED/<int:onoff>')
def whiteLED(onoff):
	print('whiteLED() onoff:', onoff)
	home.whiteLED(True if onoff else False)
	status = getStatus()
	return jsonify(status)

@app.route('/set/<paramName>/<value>')
def setParam(paramName, value):
	#print 'app.route setParam():', paramName, value
	home.setParam(paramName, value)
	config = home.getConfig()
	return jsonify(config)

@app.route('/saveconfig')
def saveConfig():
	home.saveConfigFile()
	status = getStatus()
	return jsonify(status)
	
@app.route('/loadconfigdefaults')
def loadConfig():
	home.loadConfigDefaultsFile()
	status = getStatus()
	return jsonify(status)
	
#see: https://stackoverflow.com/questions/23718236/python-flask-browsing-through-directory-with-files
@app.route('/videolist')
@app.route('/videolist/<path:req_path>')
def videolist(req_path=''):
	print('=== videolist() req_path:', req_path)
	BASE_DIR = home.videoPath + '/' #'/home/pi/video'
	
	#req_path = req_path.replace('home/pi/video/', '')
	tmpStr = BASE_DIR[1:]
	req_path = req_path.replace(tmpStr, '')
	#print '   videolist() req_path:', req_path
	
	abs_path = os.path.join(BASE_DIR, req_path)

	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		print('videolist() aborting with 404, abs_path:', abs_path)
		return "" #abort(404)
	
	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		'''
		response = make_response("")
		response.headers["X-Accel-Redirect"] = abs_path
		response.headers["Content-Type"] = mimetypes.guess_type(os.path.basename(abs_path))
		return response
		'''
		print('videolist() is serving file:', abs_path)
		return send_file(abs_path)

	# Show directory contents
	files = []
	for f in os.listdir(abs_path):
		if f == '.AppleDouble':
			continue
		f2 = f
		f = os.path.join(abs_path, f)
		fd = {'path':f, 'file':f2, 'isfile':True}
		if not os.path.isfile(f):
			files.append(fd)
		
	# load from db file
	dbFile = os.path.join(abs_path,'db.txt') 
	if os.path.isfile(dbFile):
		files2 = json.load(open(dbFile))
		for file3 in files2:
			if os.path.isfile(file3['path']):
				file3['isfile'] = True
			else:
				file3['isfile'] = False
			files.append(file3)
	
	# sort the list
	files = sorted(files, key=lambda k: k['file']) 

	print('videolist() is serving videolist.html with abs_path:', abs_path)
	return render_template('videolist.html', files=files, abs_path=abs_path)

'''
@app.route('/restart')
def restartserver():
	cmd = ['./homecage', 'restart']
	child = subprocess.Popen(cmd, shell=True) #, stdout=subprocess.PIPE)
	#out, err = child.communicate() # out is something like 'Raspberry Pi 2 Model B Rev 1.1'
	return 'flask server is restarting'
'''
	
def whatismyip():
	ips = check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

if __name__ == '__main__':	
	myip = whatismyip()
	print('homecage_app.py is running Flask server at:', 'http://' + myip + ':5000')
	debug = True
	app.run(host=myip, port=5000, debug=debug, threaded=True)
	
	
	