import sys, time
import threading
import subprocess
import Queue

def recordVideoThread(errorQueue):
	time.sleep(5)
	try:
		raise Exception('An error occured here.')
	except Exception:
		#errorQueue.put(sys.exc_info())
		errorQueue.put('recordVideoThread error')
		raise
	print('recordVideoThread stop')
	
errorQueue = Queue.Queue()

thread = threading.Thread(target=recordVideoThread, args=(errorQueue,))
thread.daemon = True							# Daemonize thread
thread.start()									# Start the execution

while True:
	try:
		exc = errorQueue.get(block=False)
	except Queue.Empty:
		pass
	else:
		print(exc)
		'''
		exc_type, exc_obj, exc_trace = exc
		# deal with the exception
		print exc_type, exc_obj
		print exc_trace
		'''