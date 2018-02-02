import subprocess

# start

if 0:
	cmd = './stream start'
	print 'cmd:', cmd
	child = subprocess.Popen(cmd, shell=True)
	out, err = child.communicate()
	print 'out:', out
	print 'err:', err

# stop
if 1:
	cmd = './stream stop'
	print 'cmd:', cmd
	child = subprocess.Popen(cmd, shell=True)
	out, err = child.communicate()
	print 'out:', out
	print 'err:', err

