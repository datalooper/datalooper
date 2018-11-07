#!/usr/bin/python

import Queue
import threading
import time

exitFlag = 0


class RecThread(threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
        self.queueLock = threading.Lock()
        self.workQueue = q

    def run(self):
        print "Starting " + self.name
        self.process_data(self.name, self.q)
        print "Exiting " + self.name

    def process_data(self, threadName, q):
        while not exitFlag:
            self.queueLock.acquire()
            if not self.workQueue.empty():
                data = q.get()
                self.queueLock.release()
                print "%s processing %s" % (threadName, data)
            else:
                self.queueLock.release()
            time.sleep(1)


threadList = ["Thread-1", "Thread-2", "Thread-3"]
nameList = ["One", "Two", "Three", "Four", "Five"]

threads = []
threadID = 1

# Create new threads
for tName in threadList:
    thread = RecThread(threadID, tName, Queue.Queue(10))
    thread.start()
    threads.append(thread)
    threadID += 1

# Fill the queue
thread.queueLock.acquire()
for word in nameList:
    workQueue.put(word)
thread.queueLock.release()

# Wait for queue to empty
while not workQueue.empty():
    pass

# Notify threads it's time to exit
exitFlag = 1

# Wait for all threads to complete
for t in threads:
    t.join()
print "Exiting Main Thread"
