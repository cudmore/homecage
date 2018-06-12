# rsync -ar --dry-run -h --info=progress2 video/20180609/ b/
# rsync -ar -h --info=progress2 video/20180609/ b/

import subprocess
import re
import sys

src = '/home/pi/video/20180609'
dst = '/home/pi/b'

#cmd = 'rsync -ar --progress ' + src + ' ' + dst
#cmd = 'rsync -ar --info=progress2 /home/pi/video/20180609 /home/pi/b'
cmd = 'rsync -ar --progress /home/pi/video/20180609 /home/pi/b'
proc = subprocess.Popen(cmd,
  shell=True,
  stdin=subprocess.PIPE,
  stdout=subprocess.PIPE,
  )

'''
output = proc.stdout.readline()
while True:
	if 1 or output:
		print('output:')
		print(output)
	output = proc.stdout.readline()
'''
line = proc.stdout.readline()
while line:
	print('line:', line)
	line = proc.stdout.readline()
