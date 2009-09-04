import time

"""
    coroutins rip through the logs, lik a chainsaw
    many many thanks to David 'Dabeaz' Beazley for http://www.dabeaz.com/coroutines/
"""

def coroutine(func):
    """ decorator function that takes care of starting a coroutine automatically on call. """
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

def follow(thefile, target):
    """ data source a la 'tail -f', feeds the coroutines """
    thefile.seek(0,2) # go to the end of the file
    while True:
         line = thefile.readline()
         if not line:
             time.sleep(0.1) # sleep briefly
             continue
         target.send(line)

@coroutine
def broadcast(targets):
    """ broadcast a stream onto multiple targets (filters) """
    while True:
        item = (yield)
        for target in targets:
            target.send(item)

@coroutine
def grep(pattern,target):
    """ a filter implemented as a coroutine """
    while True:
        line = (yield)           # Receive a line
        if pattern in line:
            target.send(line)    # Send to next stage

@coroutine
def printer():
    """ for testing only: a coroutine sink that receives data """
    while True:
         line = (yield)
         print line,

# testing/example usage
if __name__ == '__main__':
    # run logsim.py to generate "live" fake access-log
    f = open("access-log")
    p = printer()
    follow(f,
       broadcast([grep('python',p),
                  grep('ply',p),
                  grep('swig',p)])
           )
