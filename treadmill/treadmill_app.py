# 20170817
# Robert Cudmore

import os, sys, subprocess

from flask import Flask, render_template, jsonify, request
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

from treadmill import treadmill
treadmill = treadmill()

#########################################################################
@app.after_request
def myAfterRequest(response):
	if request.endpoint is None or request.endpoint in ["status", "log"]:
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
	return render_template('index.html')

@app.route('/systeminfo')
def systeminfo():
	return jsonify(treadmill.systemInfo)

@app.route('/status')
def status():
	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/startRecord')
def startRecord():
	treadmill.startRecord()
	return jsonify(treadmill.getStatus())

@app.route('/stopRecord')
def stopRecord():
	treadmill.stopRecord()
	return jsonify(treadmill.getStatus())

@app.route('/startStream')
def startStream():
	treadmill.startStream()
	return jsonify(treadmill.getStatus())

@app.route('/stopStream')
def stopStream():
	treadmill.stopStream()
	return jsonify(treadmill.getStatus())

@app.route('/startArm')
def startArm():
	treadmill.startArm()
	return jsonify(treadmill.getStatus())

@app.route('/stopArm')
def stopArm():
	treadmill.stopArm()
	return jsonify(treadmill.getStatus())

@app.route('/startTrial')
def startTrial():
	treadmill.startTrial()
	return jsonify(treadmill.getStatus())

@app.route('/stopTrial')
def stopTrial():
	treadmill.stopTrial()
	return jsonify(treadmill.getStatus())


#########################################################################
@app.route('/api/submit/saveconfig')
def saveconfig():
	treadmill.saveConfig()
	return jsonify(treadmill.getStatus())

@app.route('/api/submit/configparams', methods=['POST'])
def configparams():
	post = request.get_json()
	#print('todo: finish /api/submit/configparams')
	treadmill.updateConfig(post)
	return jsonify(treadmill.getStatus())

@app.route('/api/submit/animalparams', methods=['POST'])
def animalparams():
	post = request.get_json()
	#print('todo: finish /api/submit/configparams')
	treadmill.updateAnimal(post)
	return jsonify(treadmill.getStatus())

#########################################################################
@app.route('/api/submit/motorparams', methods=['POST'])
def motorparams():
	post = request.get_json()
	#print('/api/submit/motorparams ', post)
	treadmill.updateMotor(post)
	return jsonify(treadmill.getStatus())

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
