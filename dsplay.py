from tkinter import *
import RPi.GPIO as GPIO
import threading
import time
GPIO.setmode(GPIO.BCM)

# Debouncer
class ButtonHandler(threading.Thread):
    def __init__(self, pin, func, edge='both', bouncetime=150):
        super().__init__(daemon=True)

        self.edge = edge
        self.func = func
        self.pin = pin
        self.bouncetime = float(bouncetime)/1000

        self.lastpinval = GPIO.input(self.pin)
        self.lock = threading.Lock()

    def __call__(self, *args):
        if not self.lock.acquire(blocking=False):
            return

        t = threading.Timer(self.bouncetime, self.read, args=args)
        t.start()

    def read(self, *args):
        pinval = GPIO.input(self.pin)

        if (
                ((pinval == 0 and self.lastpinval == 1) and
                 (self.edge in ['falling', 'both'])) or
                ((pinval == 1 and self.lastpinval == 0) and
                 (self.edge in ['rising', 'both']))
        ):
            self.func(*args)

        self.lastpinval = pinval
        self.lock.release()

# The following are all of the input pin numbers using I think the bcm numbering
# This will be all the inputs for the program.
ACTION_DI = 17
ADD_CNT_DI = 5
DEC_CNT_DI = 27
RESET_CNT_DI = 18
INC_OP_CNT_DI = 12

# This sets up the pins to pull down software and changes them to input
GPIO.setup(ACTION_DI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(ADD_CNT_DI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DEC_CNT_DI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RESET_CNT_DI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(INC_OP_CNT_DI, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


## Program data and variables ##

# Number of parts cut
count = 0

# Number of operations per part
opCnt = 1

# Current opperation count
currentOp = 0

# Parts per minute Array
ppmArray=[0] * 25

# operations Per minute Array
opmArray=[0] * 25

# call to add activity into db
insAct = ()

# call to add prodtack into db
insProdtakt = ()

# The last minute that this was called
lastUpdate = int(time.time()/60)

# The current status of the machine.
# May not accurately reflect status for 5 minutes
running = False

# First of day Run Day
frod = 0

# How long we have been running today (in minutes)
runtimeVal = 0

# How long we have been stopped today (after first rod in minutes)
stoptimeVal = 0

################################


# The array is 25 long, Representing 25 minutes.
# Decisions on Start and stop times will be based on 5 minute intervals.
# If I have a 5 minute stop interval then I will add it to the
#database a Stop time
# If I have 5 minutes of production the I will set it as a start time.
# Production for the start time may be hard to estimate. I think Im
#going to define a
# Constant that says, Okay there needs to be at least 5 Operations a
#minute to qualify
# as either Start or stop time.


# Variables For the Labels in the operator interface
runtime = ()
stoptime = ()
takt = ()
op = ()
countStr = ()
runningVal = ()
stopVal = ()

# Main logic of performance indication
def timeInc():
    global lastUpdate
    if(lastUpdate != int(time.time()/60)):
        lastUpdate = int(time.time()/60)
        for x in range(24,0,-1):
            ppmArray[x] = ppmArray[x-1]
            opmArray[x] = opmArray[x-1]

        ppmArray[0] = 0
        opmArray[0] = 0
        checkRunning()
        addTaktToDB(0)
    else:
        addTaktToDB(int(time.time()/60) % 60 )

def checkRunning():
    global running
    global runtimeVal
    global stoptimeVal
    global runtime
    global stoptime
    global frod

    if(frod == 0 and ppmArray[1] > 0):
        frod = int(time.time() / 86400)

    if frod != 0:
        if frod != int(time.time() / 86400):
            frod = 0
            runtimeVal = 0
            stoptimeVal = 0

    if running:
        runtimeVal = runtimeVal + 1
        if(opmArray[1] < slowSpeed and opmArray[2] < slowSpeed and opmArray[3] < slowSpeed):
            running = False
            runtimeVal = runtimeVal - 4
            stoptimeVal = stoptimeVal + 3
            runningVal.config(bg="gray")
            stopVal.config(bg="red")
            insAct("Stop",time.time()-(60*3))
    else:
        if frod != 0:
            stoptimeVal = stoptimeVal +1
            
        if(opmArray[1]) >= runSpeed and opmArray[2] >= runSpeed and opmArray[3] >= runSpeed):
            running = True
            stoptimeVal = stoptimeVal -4
            runtimeVal = runtimeVal + 3
            runningVal.config(bg="green")
            stopVal.config(bg="gray")
            insAct("Start",time.time()-(60*3))

    runtime.set(str(int(runtimeVal/60))+":"+("%02d"%(runtimeVal%60)))
    stoptime.set(str(int(stoptimeVal/60))+":"+("%02d"%(stoptimeVal%60)))


def addTaktToDB(loctime):
    global opmArray
    global takt
    rolling = 5
    average = 0
    if ppmArray[6] != 0:
        rolling = 6
    elif ppmArray[5] != 0:
        rolling = 5
    elif ppmArray[4] != 0:
        rolling = 4
    elif ppmArray[3] != 0:
        rolling = 3
    elif ppmArray[2] != 0:
        rolling = 2
    else:
        rolling = 1
    for x in range(0,rolling):
        average = average + ppmArray[x+1]

    if(loctime != 0):
        average = ((average/rolling)*( (rolling*6)/(rolling*6 + loctime/10) ) ) + ((ppmArray[0]/(loctime/10))*((loctime/10)/(rolling*6 + loctime/10)))
    else:
        average = average/rolling
    takt.set("{0:.2f} O/m".format(average))

    if ppmArray[1] != 0 and loctime == 0:
        insProdtakt(ppmArray[1], time.time() - 60)

# Fire when an operation occurs
def opAction(val):
    global currentOp
    global opmArray
    global running
    global op
    global opCnt
    global ppmArray

    opmArray[0] = opmArray[0] + 1

    currentOp = currentOp + 1
    op.set(str(currentOp)+"/"+str(opCnt))
    if(currentOp == opCnt):
        countUp("cnt")
        ppmArray[0] = ppmArray[0] + 1
        currentOp = 0

# add one to the number of operations to produce an item
def incrementOp(val):

    global op
    global currentOp
    global opCnt
    currentOp = 0
    opCnt = opCnt % 5 + 1
    op.set(str(currentOp)+"/"+str(opCnt))

# Add one to the item count
def countUp(val):
    global count
    global countStr
    count = count + 1
    countStr.set(count)


# Take on of the item count
def countDown(val):
    global count
    global countStr
    global ppmArray
    count = count - 1
    if(count < 0):
        count = 0
    countStr.set(count)

# Reset the item count
def resetCount(val):
    global count
    global countStr
    count = 0
    countStr.set(count)

# Event Handlers
opActionHandle = ButtonHandler(ACTION_DI, opAction, edge='rising', bouncetime=120)
opActionHandle.start()

countUpHandle = ButtonHandler(ADD_CNT_DI, countUp, edge='rising', bouncetime=100)
countUpHandle.start()

countDownHandle = ButtonHandler(DEC_CNT_DI, countDown, edge='rising', bouncetime=100)
countDownHandle.start()

resetCountHandle = ButtonHandler(RESET_CNT_DI, resetCount, edge='rising', bouncetime=100)
resetCountHandle.start()

incrementOpHandle = ButtonHandler(INC_OP_CNT_DI, incrementOp, edge='rising', bouncetime=100)
incrementOpHandle.start()

# This adds interrupts to all of the inputs so that they will trigger the
# respected functions
GPIO.add_event_detect(ACTION_DI, GPIO.BOTH, callback=opActionHandle)
GPIO.add_event_detect(ADD_CNT_DI, GPIO.BOTH, callback=countUpHandle)
GPIO.add_event_detect(DEC_CNT_DI, GPIO.BOTH, callback=countDownHandle)
GPIO.add_event_detect(RESET_CNT_DI, GPIO.BOTH, callback=resetCountHandle)
GPIO.add_event_detect(INC_OP_CNT_DI, GPIO.BOTH, callback=incrementOpHandle)

# Show the main screen to check production
def showProdScreen(activityIns, prodtaktIns):

    global insAct
    global insProdtakt
    global slowSpeed
    global runSpeed

    insAct = activityIns
    insProdtakt = prodtaktIns
    slowSpeed = stopSpd
    runSpeed = runSpd

    global takt
    global op
    global countStr
    global stoptime
    global runtime
    global runningVal
    global stopVal
    # This is the main screen
    root = Tk()
    root.title("Production")

    # Set base labels for the operator interface.
    takt = StringVar()
    countStr = StringVar()
    runtime = StringVar()
    stoptime = StringVar()
    op = StringVar()

    # Set base labels for the operator interface.
    takt.set("0.0/min")
    countStr.set("0");
    runtime.set("0:00")
    stoptime.set("0:00")
    op.set("0/1")

    # Simple Frames for organizing the widgets
    top = Frame(root)
    topt = Frame(top)
    topb = Frame(top)
    left = Frame(root)
    leftl = Frame(left)
    leftr = Frame(left)
    right = Frame(root)

    # Creating Button and label widgets
    up = Button(right, text = "AddCnt", command = lambda:countUp("oi"), width = 15, font = ("Curier", 16))
    down = Button(right, text = "CntDown", command = lambda:countDown("oi"), width = 15, font = ("Curier", 16))
    reset = Button(right, text = "Reset", command = lambda:resetCount("oi"), width = 15, font = ("Curier", 16))
    runningLabel = Label(leftl, text = "Running",relief = RAISED, font= ("Curier", 20),width = 10)
    runningVal = Label(leftr, textvariable = runtime,relief = RAISED,font = ("Curier", 20),width = 5)
    stopLabel = Label(leftl, text = "Stopped",relief = RAISED, font =("Curier", 20),width = 10)
    stopVal = Label(leftr, textvariable = stoptime,relief = RAISED,font = ("Curier", 20),width = 5)
    blankl = Label(leftr, text = " ",relief = RAISED, font =("Curier", 20),width = 5)
    totall = Label(leftl, text = "Totals",relief = RAISED, font =("Curier", 20),width = 10)
    taktl = Label(topt, text = "TAKT", relief = RAISED, font =("Curier", 20), width = 10)
    eal = Label(topt, text = "OP/EA", relief = RAISED, font =("Curier", 20), width = 10)
    countl = Label(topt, text = "Count", relief = RAISED, font =("Curier", 20), width = 10)
    taktVal = Label(topb, textvariable = takt, relief = RAISED, font =("Curier", 20), width = 10)
    operationVal = Label(topb, textvariable = op ,relief = RAISED,font = ("Curier", 20), width = 10)
    countVal = Label(topb, textvariable = countStr, relief = RAISED,font = ("Curier", 20), width = 10)

    runningVal.config(bg="gray")
    stopVal.config(bg="gray")

    # Adding Widgets and frames all together
    taktVal.pack(side = LEFT );
    operationVal.pack(side = LEFT);
    countVal.pack(side = LEFT);
    taktl.pack(side = LEFT );
    eal.pack(side = LEFT);
    countl.pack(side = LEFT);
    top.pack(side = TOP)
    left.pack(side = LEFT)
    leftl.pack(side = LEFT)
    leftr.pack(side = RIGHT)
    right.pack(side = RIGHT)
    topt.pack(side = TOP)
    topb.pack(side = BOTTOM)
    totall.pack()
    blankl.pack()
    runningLabel.pack()
    runningVal.pack()
    stopLabel.pack()
    stopVal.pack()
    up.pack()
    down.pack()
    reset.pack()

    #TESTING#############################################################
    #testing = Tk()
    #testing.title("Input tester")

    #ACTION_TI = Button(testing, text = "Action", command =opActionHandle, width = 15, font = ("Curier", 16)).pack()
    #ADD_CNT_TI = Button(testing, text = "Add Cnt", command =countUpHandle, width = 15, font = ("Curier", 16)).pack()
    #DEC_CNT_TI = Button(testing, text = "Dec Cnt", command =countDownHandle, width = 15, font = ("Curier", 16)).pack()
    #RESET_CNT_TI = Button(testing, text = "Reset Cnt", command =resetCountHandle, width = 15, font = ("Curier", 16)).pack()
    #INC_OP_CNT_TI = Button(testing, text = "Inc Op", command =incrementOpHandle, width = 15, font = ("Curier", 16)).pack()
    #####################################################################
    root.mainloop()
