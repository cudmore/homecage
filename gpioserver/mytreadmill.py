import time

from gpioserver import gpioserver

class mytreadmill(gpioserver):
	def triggerIn_Callback(self, pin, index, name):
		print 'mytreadmill.triggerIn_Callback()', pin, index, name
		super(mytreadmill, self).triggerIn_Callback(pin, index, name)

	def led(self, num, on):
		super(mytreadmill, self).led(num, on)
		
		
if __name__ == '__main__':
	t = mytreadmill()
	t.led(0,True)
	time.sleep(1) # seconds
