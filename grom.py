import requests
import sys
import threading
import queue
import time
import multiprocessing

class bcolors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    OKBLUE = '\033[94m'

print(bcolors.HEADER + "[+] Built with love by ~ Elon Dusk & majksec")

class Worker (threading.Thread):
    def __init__(self, ThreadID_, function_, *args):
        threading.Thread.__init__(self)
        self.ThreadID = ThreadID_
        self.function = function_
        self.args = args

    def run(self):
        #print("Thread started with ID: {}".format(self.ThreadID))
        self.function(self.args)
        #print("Thread Finished with ID: {}".format(self.ThreadID))


class threadedFileCheck:
    def __init__(self, requestList, processQueue, processLock):
        self.exitFlag = False
        self.queueLock = threading.Lock()
        self.threadTargetAmount = 50
        self.workQueue = queue.Queue(len(requestList))
        self.workList = requestList
        self.responseQueue = processQueue
        self.pLock = processLock

        self.threadedCheck()

    def threadProcessData(self, threadID_):
        while not self.exitFlag:
            self.queueLock.acquire()
            if not self.workQueue.empty():
                reqLine = self.workQueue.get()
                self.queueLock.release()
                #print("thread-%s started check on %s" % (str(threadID_[0]), str(reqLine)))
                self.threadCheckLine(reqLine)
            else:
                self.queueLock.release()
                time.sleep(.5)

    def threadCheckLine(self, clean_line): #returns responsive sites as list with response codes
        clean_line = clean_line.strip()
        try:
            response = requests.get(clean_line, timeout=(3))

            if response.status_code == 200:
                
                print(bcolors.OKGREEN + "[+] {} is up {}".format(clean_line, response))

                self.pLock.acquire()

                self.responseQueue.put(clean_line + " [200]")

                self.pLock.release()

            else:
                print(bcolors.OKBLUE + "[+] {} is up with code {}".format(clean_line, response.status_code))

        except:
            print(bcolors.FAIL + "[-]{} is not reachable".format(clean_line))

        

    def threadedCheck(self):

        threads = []

        #create threads
        for i in range(self.threadTargetAmount):
            thread = Worker(i, self.threadProcessData, i)
            thread.start()
            threads.append(thread)

        self.queueLock.acquire()

        for line in self.workList:
            self.workQueue.put(line)
        self.queueLock.release()

        while not self.workQueue.empty():
            pass

        self.exitFlag = True

        for t in threads:
            t.join()


def outputToFile(_list, filename):
    with open(filename, 'w') as f:
        for item in _list:
            f.write("%s\n" % item)

def getFileAsList(filename):
    rList = []
    with open(filename, "r") as fileObj:
        for line in fileObj.readlines():
            rList.append(line.strip())
    return rList

def parts(L, n): 
    
    q, r = divmod(len(L), n)
    I = [q*i + min(i, r) for i in range(n+1)]
    return [L[I[i]:I[i+1]] for i in range(n)]


def addHeaders(list_):
    output = []
    for line in list_:
        output.append("https://"+line)
        output.append("http://"+line)
    return output

if __name__ == "__main__":

    requestList = getFileAsList(sys.argv[1])

    requestList = addHeaders(requestList)

    targetProcessAmount = multiprocessing.cpu_count()

    processQueue = multiprocessing.Queue(len(requestList))
    processLock = multiprocessing.Lock()

    processes = []

    slicedRequests = parts(requestList, targetProcessAmount)

    for i in range(targetProcessAmount):

        process = multiprocessing.Process(target=threadedFileCheck, args=(slicedRequests[i], processQueue, processLock))

        process.start()

        processes.append(process)
    outputList = []

    liveprocs = True

    while liveprocs or not processQueue.empty():
        try:
            while not processQueue.empty():
                outputList.append(processQueue.get())
        except:
            pass

        liveprocs = False
        for p in processes:
            if p.is_alive():
                liveprocs = True
                break
        time.sleep(.25)

    for p in processes:
        p.join()

    while not processQueue.empty():
        outputList.append(processQueue.get())

    outputToFile(outputList, sys.argv[2])

    print("program finished successfully")
