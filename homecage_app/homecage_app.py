#!/usr/bin/env python

from flask import Flask, render_template, send_file, jsonify
import subprocess
from datetime import datetime

# turn off printing to console
if 1:
	import logging
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

from home import home

home = home()

app = Flask(__name__)

def getStatus():
	# Get struct of status from the backend
	status = home.getStatus()
	return status
	
@app.route('/')
def hello_world():
	return render_template('index.html')

# help
@app.route('/help')
def dispHelp():
	return render_template('help.html')

# state of server, queried about every second
@app.route('/status')
def status():	
	#print 'status()'
	theStatus = getStatus()
	#print '   theStatus:', theStatus
	return jsonify(theStatus)
	
# params that can be set by the user
@app.route('/params')
def params():
	print 'params()'
	
	status = home.getParams()
	return jsonify(status)
	
@app.route('/lastimage')
def lastimage():
	myImage = 'static/still.jpg'
	return send_file(myImage)
	
@app.route('/record/<int:onoff>')
def record(onoff):
	print 'record() onoff:', onoff
	home.record(onoff)

	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)
	
@app.route('/stream/<int:onoff>')
def stream(onoff):
	print 'stream() onoff:', onoff
	home.stream(onoff)

	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)
	
@app.route('/irLED/<int:onoff>')
def irLED(onoff):
	print 'irLED() onoff:', onoff
	home.irLED(onoff)

	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)
	
@app.route('/whiteLED/<int:onoff>')
def whiteLED(onoff):
	print 'whiteLED() onoff:', onoff
	home.whiteLED(onoff)

	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)

@app.route('/set/<paramName>/<int:value>')
def setParam(paramName, value):
	print '\n\tsetParam():', paramName, value, '\n'
	if paramName == 'fps':
		home.fps = value
	if paramName == 'fileDuration':
		home.fileDuration = value

	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)

def whatismyip():
	arg='ip route list'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	ipaddr = split_data[split_data.index('src')+1]
	return ipaddr

if __name__ == '__main__':
	print 'Running Flask server at:', 'http://' + whatismyip() + ':5000'
	app.run(host=whatismyip(), port=5000, debug=False)
	
	
	