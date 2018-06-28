# 20170817
# Robert Cudmore

import os, sys, time, subprocess

from flask import Flask, render_template, send_file, jsonify, request, Response
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

#########################################################################
app = Flask('treadmill_app')
#app = Flask(__name__)
CORS(app)

logHandler = FileHandler('logs/treadmill.log', mode='w')
logHandler.setLevel(logging.DEBUG)
myFormatter = logging.Formatter(logFormat)
logHandler.setFormatter(myFormatter)
app.logger.addHandler(logHandler)	

app.logger.setLevel(logging.DEBUG)

# turn off werkzeug logging
werkzeugLogger = logging.getLogger('werkzeug')
werkzeugLogger.setLevel(logging.ERROR)

from treadmill import treadmill
treadmill = treadmill()

#########################################################################
@app.after_request
def myAfterRequest(response):
	if request.endpoint is None or request.endpoint in ["status", "log", "static"]:
		# ignore
		pass
	else:
		#request.endpoint is name of my function (not web address)
		#print(request.url)
		app.logger.debug('after ' + request.path)
	return response

#########################################################################
@app.route('/')
def hello_world():
	return send_file('templates/index.html')

@app.route('/templates/partials/<path:htmlfile>')
def templates(htmlfile):
	#print('htmlfile:', htmlfile)
	return send_file('templates/partials/' + htmlfile)

@app.route('/systeminfo')
def systeminfo():
	return jsonify(treadmill.systemInfo)

@app.route('/log')
def log():
	with open('logs/treadmill.log', 'r') as f:
		return Response(f.read(), mimetype='text/plain')

@app.route('/environment')
def environment():
	return send_file('templates/environment.html')

@app.route('/environmentlog')
def environmentlog():
	with open('logs/environment.log', 'r') as f:
		return Response(f.read(), mimetype='text/plain')

@app.route('/status')
def status():
	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/api/action/<string:thisAction>')
def action(thisAction):

	#print('*** /api/action/' + thisAction)
	
	if thisAction == 'startRecord':
		treadmill.startRecord()
	if thisAction == 'stopRecord':
		treadmill.stopRecord()

	if thisAction == 'startStream':
		treadmill.startStream()
	if thisAction == 'stopStream':
		treadmill.stopStream()

	if thisAction == 'startArm':
		treadmill.startArm()
	if thisAction == 'stopArm':
		treadmill.stopArm()

	if thisAction == 'startArmVideo':
		treadmill.startArmVideo()
	if thisAction == 'stopArmVideo':
		treadmill.stopArmVideo()

	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/api/submit/<string:submitThis>', methods=['GET', 'POST'])
def submit(submitThis):
	post = request.get_json()

	if submitThis == 'saveconfig': # GET
		treadmill.saveConfig()

	if submitThis == 'configparams':
		treadmill.updateConfig(post)
	if submitThis == 'animalparams':
		treadmill.updateAnimal(post)
	if submitThis == 'ledparams':
		treadmill.updateLED(post)
	if submitThis == 'motorparams':
		treadmill.updateMotor(post)

	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/api/eventout/<name>/<int:onoff>')
def eventOut(name, onoff):
	''' turn named output pin on/off '''
	treadmill.trial.eventOut(name, True if onoff else False)
	return jsonify(treadmill.getStatus())

@app.route('/api/simulate/starttrigger')
def simulate_starttrigger():
	# todo: remove pin from triggerIn_Callback
	tmpPin = None
	treadmill.trial.triggerIn_Callback(tmpPin)
	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/videolist')
@app.route('/videolist/<path:req_path>')
def videolist(req_path=''):
	# serve a list of video files
	
	# we need to append '/' so os.path.join works???
	savePath = treadmill.trial.config['trial']['savePath'] + '/'
	
	tmpStr = savePath[1:]
	req_path2 = req_path.replace(tmpStr, '')
	#req_path2 = req_path2.replace('/', '') # why do i need this?
	
	abs_path = os.path.join(savePath, req_path2)

	# What the fuck happened here?
	'''
	print('req_path:', req_path)
	print('savePath:', savePath)
	print('req_path2:', req_path2)
	print('abs_path:', abs_path)
	'''
	
	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		app.logger.error('videolist() aborting with 404, abs_path: ' + abs_path)
		return "" #abort(404)
	
	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		app.logger.debug(('videolist() is serving file:', abs_path))
		return send_file(abs_path)

	# Show directory contents
	files = []
	for f in os.listdir(abs_path):
		if f.startswith('.') or f in ['Network Trash Folder', 'Temporary Items']:
			continue
		f2 = f
		f = os.path.join(abs_path, f)
		
		fileDict = {}
		
		isTrialFile = f.endswith('.txt') # big assumption, should parse '_r%d.txt'
		'''
		if isTrialFile:
			fileDict = home.trial.loadTrialFile(f)
		'''
		
		# get file size in either MB or KB (if <1 MB)
		unitStr = 'MB'
		size = os.path.getsize(f)
		sizeMB = size/(1024*1024.0) # mb
		if sizeMB < 0.1:
			unitStr = 'bytes'
			sizeMB = size
		sizeStr = "%0.1f %s" % (sizeMB, unitStr)
		
		#fd = {'path':f, 'file':f2, 'isfile':True, 'size':sizeStr}
		fileDict['path'] = f
		fileDict['file'] = f2
		fileDict['isFile'] = True
		fileDict['size'] = sizeStr
		fileDict['cTime'] = time.strftime('%Y%m%d %H%M%S', time.localtime(os.path.getctime(f)))
		fileDict['mTime'] = time.strftime('%Y%m%d %H%M%S', time.localtime(os.path.getmtime(f)))
		files.append(fileDict)
		
	# sort the list
	files = sorted(files, key=lambda k: k['file']) 

	return render_template('videolist.html', files=files, abs_path=abs_path, systemInfo=treadmill.systemInfo)

#########################################################################
def whatismyip():
	ips = subprocess.check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

if __name__ == '__main__':	
	myip = whatismyip()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	app.logger.debug('Running flask server with debug = ' + str(debug))
		
	responseStr = 'Flask server is running at: ' + 'http://' + str(myip) + ':5010'
	app.logger.debug(responseStr)
	
	# 0.0.0.0 will run on external ip	
	app.run(host='0.0.0.0', port=5010, debug=debug, threaded=True)
