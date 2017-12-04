import os, subprocess
from datetime import datetime

from flask import Flask, render_template, send_file, jsonify, redirect, abort
from flask_cors import CORS

# turn off printing to console
if 1:
	import logging
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)

from home import home

home = home()

app = Flask(__name__)
CORS(app)

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
	home.setParam(paramName, value)
	
	status = getStatus()
	#return jsonify(status=list(status.items()))
	return jsonify(status)

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
	print 'videolist() req_path:', req_path
	BASE_DIR = '/home/pi/video'
	
	req_path = req_path.replace('home/pi/video/', '')
	print '   xxx videolist() req_path:', req_path
	
	abs_path = os.path.join(BASE_DIR, req_path)

	# Return 404 if path doesn't exist
	if not os.path.exists(abs_path):
		return abort(404)
	
	# Check if path is a file and serve
	if os.path.isfile(abs_path):
		return send_file(abs_path)

	# Show directory contents
	#files = os.listdir(abs_path)
	#files = [os.path.join(abs_path, f) for f in os.listdir(abs_path) if f.endswith('.mp4') or not os.path.isfile(f)]
	files = []
	for f in os.listdir(abs_path):
		if f == '.AppleDouble':
			continue
		f2 = f
		f = os.path.join(abs_path, f)
		fd = {'path':f, 'file':f2}
		if not os.path.isfile(f):
			files.append(fd)
		elif f.endswith('.mp4'):
			print fd
			files.append(fd)
	#print files
	# sort the list
	files = sorted(files, key=lambda k: k['file']) 
	return render_template('videolist.html', files=files, abs_path=abs_path)

	#files = os.listdir('/home/pi/video')
	#return render_template('videolist.html', files=files)
	
'''
@app.route('/servevideo/<path:req_path>')
def servevideo(req_path):
	BASE_DIR = '/home/pi/video/mp4'
	abs_path = os.path.join(BASE_DIR, req_path)
	#return send_file(abs_path)
	print 'servevideo(): req_path:', req_path, 'abs_path:', abs_path
	#return redirect(abs_path)
	return send_file(abs_path)
'''
	
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
	
	
	