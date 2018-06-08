from __future__ import print_function	# (at top of module)

import os, sys, json
from datetime import datetime
from subprocess import check_output

#import mimetypes # to send files to ios

from flask import Flask, render_template, send_file, jsonify, abort, request, Response #, redirect, make_response
from flask_cors import CORS

import logging
from logging import FileHandler #RotatingFileHandler

from logging.config import dictConfig

logFormat = "[%(asctime)s] {%(filename)s %(funcName)s:%(lineno)d} %(levelname)s - %(message)s"
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': logFormat,
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask('homecage_app')
#app = Flask(__name__)
CORS(app)

logHandler = FileHandler('log.log', mode='w')
logHandler.setLevel(logging.DEBUG)
myFormatter = logging.Formatter(logFormat)
logHandler.setFormatter(myFormatter)
app.logger.addHandler(logHandler)	

app.logger.setLevel(logging.DEBUG)

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)

#
import bUtil
from home import home
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
	if request.endpoint is None or request.endpoint in ["status", "lastimage", "log"]:
		# ignore
		pass
	else:
		#request.endpoint is name of my function (not web address)
		#print(request.url)
		app.logger.debug('after ' + request.path + ' state:' + home.state)
	return response

@app.errorhandler(404)
def page_not_found(e):
	#return render_template('404.html'), 404
	return 'Error 404: File not found. This happens when you manually delete video files.'
		
@app.route('/')
def hello_world():
	#app.logger.debug('/')
	home.getSystemInfo() # update cpu temp, disk space, ip
	return render_template('index.html')

@app.route('/log')
def log():
	with open('log.log', 'r') as f:
		return Response(f.read(), mimetype='text/plain')
		
@app.route('/help')
def dispHelp():
	return render_template('help.html')

@app.route('/status')
def status():	
	# state of server, queried about every second
	theStatus = getStatus()
	return jsonify(theStatus)
	
@app.route('/config')
def config():
	# params that can be set by the user
	#print 'app.route config()'
	status = home.getConfig()
	return jsonify(status)
	
@app.route('/lastimage')
def lastimage():
	myImage = 'static/still.jpg'
	return send_file(myImage)
	
@app.route('/record/<int:onoff>')
def record(onoff):
	#turn recording on/off
	home.record(onoff)

	status = getStatus()
	return jsonify(status)
	
@app.route('/stream/<int:onoff>')
def stream(onoff):
	#turn streaming on/off
	home.stream(onoff)
	status = getStatus()
	return jsonify(status)
	
@app.route('/arm/<int:onoff>')
def arm(onoff):
	#turn arm on/off (when armed will start video on GPIO triggerIn
	home.arm(onoff)
	status = getStatus()
	return jsonify(status)

@app.route('/simulate/triggerin')
def sim_triggerin():
	home.triggerIn_Callback(1)
	return jsonify(getStatus())
	
@app.route('/simulate/frame')
def sim_frame():
	#home.frame_Callback(1)
	home.eventIn_Callback('frame')
	return jsonify(getStatus())

@app.route('/simulate/stop')
def sim_stop():
	home.stop()
	return jsonify(getStatus())
	
@app.route('/api/eventout/<name>/<int:onoff>')
def eventOut(name, onoff):
	''' turn named output pin on/off '''
	home.eventOut(name, True if onoff else False)
	return jsonify(getStatus())
	
'''
@app.route('/irLED/<int:onoff>')
def irLED(onoff):
	#print('irLED() onoff:', onoff)
	home.irLED(True if onoff else False)
	status = getStatus()
	return jsonify(status)
	
@app.route('/whiteLED/<int:onoff>')
def whiteLED(onoff):
	#print('whiteLED() onoff:', onoff)
	home.whiteLED(True if onoff else False)
	status = getStatus()
	return jsonify(status)
'''

@app.route('/set/<paramName>/<value>')
def setParam(paramName, value):
	app.logger.debug(paramName + "'" + value + "'")
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
	# serve a list of video files
	BASE_DIR = home.videoPath + '/' #'/home/pi/video'
	
	#req_path = req_path.replace('home/pi/video/', '')
	tmpStr = BASE_DIR[1:]
	req_path = req_path.replace(tmpStr, '')
	
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
		app.logger.debug(('videolist() is serving file:', abs_path))
		return send_file(abs_path)

	# Show directory contents
	files = []
	for f in os.listdir(abs_path):
		if f in ['.AppleDouble', '.DS_Store']:
			continue
		f2 = f
		f = os.path.join(abs_path, f)
		
		# get file size in either MB or KB (if <1 MB)
		unitStr = 'MB'
		size = os.path.getsize(f)
		sizeMB = size/(1024*1024.0) # mb
		if sizeMB < 0.1:
			unitStr = 'bytes'
			sizeMB = size
		sizeStr = "%0.1f %s" % (sizeMB, unitStr)
		
		fd = {'path':f, 'file':f2, 'isfile':True, 'size':sizeStr}
		files.append(fd)
		'''
		if not os.path.isfile(f):
			files.append(fd)
		'''
		
	# load from db file
	'''
	dbFile = os.path.join(abs_path,'db.txt') 
	if os.path.isfile(dbFile):
		files2 = json.load(open(dbFile))
		for file3 in files2:
			if os.path.isfile(file3['path']):
				file3['isfile'] = True
			else:
				file3['isfile'] = False
			files.append(file3)
	'''
	
	# sort the list
	files = sorted(files, key=lambda k: k['file']) 

	return render_template('videolist.html', files=files, abs_path=abs_path, systemInfo=home.systemInfo)

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
	#myip = whatismyip()
	myip = bUtil.whatismyip_safe()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	app.logger.debug('Running flask server with debug = ' + str(debug))
		
	app.logger.debug('Flask server is running at: ' + 'http://' + str(myip) + ':5000')
	
	# 0.0.0.0 will reun on external ip and needed to start at boot with systemctl
	# before we get a valid ip from whatismyip()
	
	app.run(host='0.0.0.0', port=5000, debug=debug, threaded=True)
	
	
	