from __future__ import print_function    # (at top of module)

import os, subprocess, json

'''
cmd = 'xxx'
try:
	out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
	print('out:', out)
except OSError as e:
	print('e:', e)
'''

"""
cmd = ['./avprobe_video.sh', '/home/pi/video/20180604/20180604_221209_t1_r1.mp4']
try:
	out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
except OSError as e:
	print('e:', e)
	print('e.returncode:', e.returncode) # 1 is failure, 0 is sucess
	print('e.output:', e.output)
	#pass

out = json.loads(out)
#print('avprobe out:', out)


print(out['streams'][0]['duration'])
"""

import picamera
camera = picamera.PiCamera()
while True:
	pass
