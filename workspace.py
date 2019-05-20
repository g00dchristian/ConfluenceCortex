from threading import Thread
import time


'''

def function(input, number, result):
	x = input*2*84878289
	result.update({number: x})


class Tester():
	"""docstring for Tester"""
	def __init__(self):
		self.result={}
		self.funky()

	def funky(self):
		threads = []
		for x in range(100):
			launch = Thread(target=function, args=[4, x, self.result])
			launch.start()
			threads.append(launch)

		for process in threads:
			process.join()

		for x in self.result:
			print(x, self.result[x])


Tester()

'''


row=[1,2,3]

def funk(ins):
	outs=[]
	outs.append(ins)
	outs.append([2,3,4])
	print(ins)

def funkyy(ins):
	ins.append([2,3,4])
	print(ins)


funk(row)
funkyy(row)





