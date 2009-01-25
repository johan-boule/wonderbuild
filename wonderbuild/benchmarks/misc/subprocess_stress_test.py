#! /usr/bin/env python

if __name__ == '__main__':

	import threading, subprocess, time
	
	thread_count = 2
	input = 'test\n'
	args = ['cat']
	
	input = None
	args = ['cat', '/tmp/t']
	
	def thread_function(input, args):
		while True:
			p = subprocess.Popen(
				args = args,
				bufsize = -1,
				stdin = input and subprocess.PIPE,
				stdout = subprocess.PIPE,
				stderr = subprocess.PIPE,
			)
			out, err = p.communicate(input)
			print p.returncode, time.time()

	threads = []
	for i in xrange(thread_count):
		t = threading.Thread(target = thread_function, args = (input, args), name = 'thread-' + str(i))
		#t.daemon = True
		t.setDaemon(True)
		t.start()
		threads.append(t)
		
	for t in threads: t.join(timeout = 3600.0)
