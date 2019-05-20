from threading import Thread
import time
import uuid

results = [{} for x in range(100)]

def crawl(input1):
	time.sleep(1)
	results[input1]=time.time()
	return input1 

pics={}
threads = []

for x in range(100):
	pics[x] = Thread(target=crawl, args=[x])
	pics[x].start()
	threads.append(pics[x])

for process in threads:
	process.join()


print(pics)


