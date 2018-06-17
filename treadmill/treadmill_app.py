# 20170817
# Robert Cudmore

import os, sys, subprocess

from flask import Flask, render_template, jsonify
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

from treadmill import treadmill
treadmill = treadmill()

@app.route('/')
def hello_world():
	#app.logger.debug('/')
	treadmill.home.getSystemInfo() # update cpu temp, disk space, ip
	return render_template('index.html')

@app.route('/systeminfo')
def systeminfo():
	return jsonify(treadmill.home.systemInfo)
	
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
