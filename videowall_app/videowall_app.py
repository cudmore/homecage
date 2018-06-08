# Robert Cudmore
# 20180101

from __future__ import print_function    # (at top of module)

import sys, subprocess
import json

from flask import Flask, render_template, send_file, jsonify, abort#, redirect, make_response
from flask_cors import CORS
from subprocess import check_output

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
	print('saveconfig()')
	print('   configfile:', configfile)
	with open('config_videowall.json', 'w') as outfile:
		json.dump(configfile, outfile, indent=4)
	return 'saved'
	
@app.route('/loadconfig')
def loadconfig():
	print('loadconfig()')
	configfile = ''
	with open('config_videowall.json') as configFile:
		configfile = json.load(configFile)
	print('configfile:', configfile)
	#return jsonify(configfile)
	return configfile
	
'''
def whatismyip():
	arg='ip route list'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	ipaddr = split_data[split_data.index('src')+1]
	return ipaddr
'''

def whatismyip():
	ips = check_output(['hostname', '--all-ip-addresses'])
	ips = ips.decode('utf-8').strip()
	return ips

if __name__ == '__main__':
	myip = whatismyip()
	
	debug = False
	if len(sys.argv) == 2:
		if sys.argv[1] == 'debug':
			debug = True
	app.logger.debug('Running flask server with debug = ' + str(debug))
		
	responseStr = 'Flask server is running at: ' + 'http://' + str(myip) + ':8000'
	print(responseStr)
	app.logger.debug(responseStr)
	
	# 0.0.0.0 will run on external ip and needed to start at boot with systemctl
	# before we get a valid ip from whatismyip()
	
	app.run(host='0.0.0.0', port=8000, debug=debug, threaded=True)

