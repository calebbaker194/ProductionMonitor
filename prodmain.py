import dsplay
import pgdrive
import time
from threading import Thread

running = True

def dbIsRegister():
    global running
    print("Starting ProdScreen")
    t2 = Thread(target = dsplay.showProdScreen, args=(pgdrive.insertActivity,pgdrive.insertprodtakt))
    t2.start()
    print("Entering Main Loop")
    t1 = Thread(target = timeStep)
    t1.start()
    
def timeStep():
    try:
        while running:
            # Get the current Time
            cTime = time.time()
            # Wait until the beginning of the next minute
            time.sleep(10-(cTime%10))
            # Increment the Takt Keeper
            dsplay.timeInc()
    except KeyboardInterrupt:
        pass

pgdrive.register(dbIsRegister)

