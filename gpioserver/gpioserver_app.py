# 20180424

# gpio server app

import subprocess

from flask import Flask, jsonify

#from gpioserver import gpioserver
from mytreadmill import mytreadmill

global myserver
#myserver = gpioserver()
myserver = mytreadmill()

app = Flask(__name__)

@app.route('/')
def hello_world():
	return jsonify(myserver.getStatus())

@app.route('/status')
def getStatus():
	return jsonify(myserver.getStatus())
	
@app.route('/config')
def getConfig():
	return jsonify(myserver.getConfig())
	

@app.route('/led/<int:idx>/<int:on>')
def led(idx,on):
	myserver.led(idx,True if on else False)
	return ""
	
def whatismyip():
	arg='ip route list'
	p=subprocess.Popen(arg,shell=True,stdout=subprocess.PIPE)
	data = p.communicate()
	split_data = data[0].split()
	ipaddr = split_data[split_data.index('src')+1]
	return ipaddr

if __name__ == '__main__':
	print 'Running Flask server at:', 'http://' + whatismyip() + ':5000'
	app.run(host=whatismyip(), port=5000, debug=True, threaded=True)
	
