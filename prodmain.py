import dsplay
import socket
import time
import sys
from threading import Thread

running = True

def get_lock(process_name):
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        get_lock._lock_socket.bind('\0'+process_name)
        print("Lock Acquired Starting program")
    except socket.error:
        print("Could not Acquire Lock. Program Shutting Down")
        sys.exit();

def dbIsRegister():
    global running
    print("Starting ProdScreen")
    dsplay.main_close = on_close
    t2.start()
    while not(dsplay.IsConfig):
        time.sleep(1)
    print("Entering Main Loop")
    t1.start()
    
def timeStep():
    try:
        while running:
            # Get the current Time
            cTime = time.time()
            # Wait until the beginning of the next second
            time.sleep(1-(cTime%1))
            # Increment the Takt Keeper
            dsplay.timeInc()
    except KeyboardInterrupt:
        pass

def on_close():
    global running
    running = False
    
t2 = Thread(target = dsplay.showProdScreen)
t1 = Thread(target = timeStep)
get_lock('prodmon')
dsplay.register(dbIsRegister)

