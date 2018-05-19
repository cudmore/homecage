import subprocess
import json

from flask import Flask, render_template, send_file, jsonify, abort#, redirect, make_response
from flask_cors import CORS

# turn off printing to console
if 1:
	import logging
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

app = Flask(__name__)
CORS(app)

def getStatus():
	# Get struct of status from the backend
	status = home.getStatus()
	return status
	
@app.route('/')
def hello_world():
	return render_template('index.html')

@app.route('/saveconfig/<configfile>')
def saveconfig(configfile):
	print 'saveconfig()'
	print '   configfile:', configfile
	with open('config_videowall.json', 'w') as outfile:
		json.dump(configfile, outfile, indent=4)
	return 'saved'
	
@app.route('/loadconfig')
def loadconfig():
	print 'loadconfig()'
	configfile = ''
	with open('config_videowall.json') as configFile:
		configfile = json.load(configFile)
	print configfile
	return jsonify(configfile)
	
def whatismyip():
	arg='ip route list'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	ipaddr = split_data[split_data.index('src')+1]
	return ipaddr

if __name__ == '__main__':
	print 'videoserver.py is running Flask server at:', 'http://' + whatismyip() + ':8000'
	debug = True
	app.run(host=whatismyip(), port=8000, debug=debug, threaded=True)
