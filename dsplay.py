from tkinter import *
from tkinter import ttk
import queue
import RPi.GPIO as GPIO
import threading
import time
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.animation as animation
import matplotlib.dates as mdate
from matplotlib import style
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
ppmArray= queue.Queue()

# operations Per minute Array
opmArray= queue.Queue()

for popx in range(25):
    ppmArray.put(0)
    opmArray.put(0)

# Parts In the current Minute
ppmCnt = 0

# Operations in the current Minute
opmCnt = 0

# call to add activity into db
insAct = ()

# call to add prodtack into db
insProdtakt = ()

# The last minute that this was called
lastUpdate = int(time.time()%60)

# The current status of the machine.
# May not accurately reflect status for 5 minutes
running = False

# First of day Run Day
frod = 0

# How long we have been running today (in minutes)
runtimeVal = 0

#
stoptimeVal = 0

# how much time the last loockBackDist operations must occur in to be running
lookBackTime = 0

# how many operations to look back
lookBackDist = 0

# the running speed threshold
runSpeed = 0

# Runtime = runBase + time.time() - currRunStart
# on Stop: runBase = lastStopTime - currRunStart then currRunStart = 0
# if running this will = the time the machine started running
currRunStart = 0

# the sum of all the run times not including the curr run time
runBase = 0

# this is the stop time to inserte into the database
lastStopTime = 0

# the sum of all stop times other then the current stop cycle
stopBase = 0 

# An array of time stamps that represent the part creations to calculate the takt time
eatime = queue.Queue()

# Data For the graphs
graphXData = queue.Queue()

graphYData = queue.Queue()

for tmpcnt in range (600): # set the distance back the graph looks in seconds
    graphXData.put(matplotlib.dates.epoch2num(time.time()-(600-tmpcnt)))
    graphYData.put(0)

graphFigure = ()

# Store the last checked takt time
lastTakt = 0

#
taktval = 0

# The variable for the graph in the graphing screen
graph = ()

################################

# Variables For the Labels in the operator interface
runtime = ()
stoptime = ()
takt = ()
op = ()
countStr = ()
runningVal = ()
stopVal = ()
efficiency = ()

# Main logic of performance indication will occure every second to keep run time and stop time live
def timeInc():

    global lastUpdate
    global ppmCnt
    global opmCnt

    onminute = (lastUpdate != int(time.time()%3600/60))

    if((int(time.time())%60)%10 == 0):# If the second is a multiple of 10
        calcTakt() # refresh the takt time
    
    checkRunning(onminute) # Check running (True Or False) True if it is on the minute

    if(onminute): # On the Minute

        addTaktToDB() # Adds the parts produced to the database unless it == 0
        
        lastUpdate = int(time.time()%3600/60) # Update the last time the Production was added
        
        ppmArray.put(ppmCnt)
        opmArray.put(opmCnt)
        opmArray.get()
        ppmArray.get()

        ppmCnt = 0 # Set the current minute to 0
        opmCnt = 0 # 

        

def checkRunning(onMinute):
    
    global running
    global runtimeVal
    global stoptimeVal
    global lookBackDist
    global lookBackTime
    global lastStopTime
    global frod
    global currRunStart
    global runBase
    global eatime
    global stopBase
    global efficiency
    global lastTakt
    global taktval
    global graphXData
    global graphYData

    lastTakt = lastTakt + (.1*(taktval - lastTakt))
    
    graphXData.put(matplotlib.dates.epoch2num(time.time()))
    graphXData.get()
    graphYData.put(lastTakt)
    graphYData.get()

    if(frod == 0 and list(ppmArray.queue)[1] > 0): # If there has been no run today and parts were produced this minute.
        frod = int(time.time() / 86400) # Set the first run of the day to today

    if frod != 0: # If the machine has been run today
        if frod != int(time.time() / 86400): # check to so see if the days match
            frod = 0 # If the do not then set the program to no runs today And reset the running and stop counters
            runtimeVal = 0
            runBase = 0
            lastStopTime = 0
            stopBase = 0
            currRunStart = 0
            stoptimeVal = 0

    if running: # If the program is in the running state
        runtimeVal = runBase + (time.time() - currRunStart) # update the run time to the currrent running time
        if(isStopped()): # Check to see if the program is stopped and if it is set the lastSopTime
            running = False # set the running flag to false
            runBase = runBase + (lastStopTime - currRunStart) # Set run Base = to all the previous run times plus the current ending run time
            eatime= queue.Queue() # reset the operation queue that calculates takt time
            runtimeVal = runBase # Set the displayed runtime value to the correct run time
            stoptimeVal = stopBase + (time.time() - lastStopTime) # set the stoptime value to the previus stops plus the current added stop
            currRunStart = 0 # resest the start time of the current run to 0
            runningVal.config(bg="gray") # change colors
            stopVal.config(bg="red") #
            insAct("Stop",lastStopTime) # Insert Stop Time in database
    else: # If the program is in the stopped state
        if frod != 0: # If there Has been a run today
            stoptimeVal = stopBase + (time.time() - lastStopTime) # Update the Stop Time Displayed
            
        if (isRunning()) : # Check to see if the machine is running and set currRunStart if it is.
            running = True # set running flag to True
            if lastStopTime != 0: # Check to make sure that we have stopped today To avoid counting the time since 12AM
                stopBase = stopBase + (currRunStart - lastStopTime) # add this stop to the sum of stop time
            lastStopTime = 0 # reset the last Stop Time
            stoptimeVal = stopBase # Chage the display value
            runtimeVal = runBase + (time.time() - currRunStart) # change the running display to the run time plus the current run 
            runningVal.config(bg="green") # Color Change
            stopVal.config(bg="gray") #
            insAct("Start",currRunStart) # Add A Start Time to the Database

    if stoptimeVal > 0:
        efficiency.set(str("%01d"%(int(runtimeVal/(stoptimeVal+runtimeVal)*100)))+"%")
    elif runtimeVal > 0:
        efficiency.set("100%")
    else:
        efficiency.set("0%")
    runtime.set(str("%02d"%int(runtimeVal/3600))+":"+("%02d"%(runtimeVal%3600/60))+":"+("%02d"%(runtimeVal%60))) # update display with proper values
    stoptime.set(str("%02d"%int(stoptimeVal/3600))+":"+("%02d"%(stoptimeVal%3600/60))+":"+("%02d"%(stoptimeVal%60)))

def isStopped():
    global eatime
    global lookBackTime
    global lastStopTime
    
    l = list(eatime.queue) # Take all the operation time stamps and put them in a list
    l.sort(reverse=True) # sord the list most recent to oldest

    for x in l: # loop through the list. But we only look at the first one
        if x < time.time() - 60 * lookBackTime: # if the most recent stamp is older then (lookBackTime) minutes
            lastStopTime = x # set the stop here 
        return x < time.time() - 60 * lookBackTime # return if the most recent punch is too old to be running.

def animate(objData):
    graph.plot(list(graphXData.queue), list(graphYData.queue), 'C3')
    

def isRunning():
    global eatime
    global lookBackDist
    global lookBackTime
    global currRunStart
    global lookBackDist
    
    count = 1 # count of the number of operations in the time window
    if(eatime.qsize() < lookBackDist): # if the queue of time stamps isnt long enough to determin a run
        return False; # return that the machine is not running

    l = list(eatime.queue) # turn the queue into a list
    l.sort(reverse=True) # sort from newst to oldest punches

    for x in l: # Loop through the list
        if count >= lookBackDist: # if count > = lookBackDist (The number of stamps that must fall in the time window)
            currRunStart = x # Set the start equal to the first stamp in the window 
            break # exit the loop
        if x < (time.time() - (lookBackTime * 60)): # if the time stamp is older the the window
            return False # return false
        count = count + 1 # increment count by one for the matched time stamp
            

    return count >= lookBackDist  # return true of there are enough stamps in the time window

def addTaktToDB():
    global ppmCnt 
    
    if ppmCnt != 0: # If there were parts produced last minute
        insProdtakt(ppmCnt, time.time() - 60) # insert the number of parts produced last mintute


# Calc Takt time and display on the monitor also remove old times
def calcTakt():
    global eatime
    global takt
    global lookBackTime
    global taktval
    
    l = [] # the list to store elements the should be added back to the queue
    sumtime = 0 # the sum of all the punches in the eatime queue
    oldesttime = time.time() # find the oldest punch in the list

    if eatime.qsize() == 0:
        takt.set("{0:.2f} /min".format(0))
        return;
    
    while eatime.qsize() > 0: # while the queue has elements left
        t = eatime.get() # set t equal to an elemnt that you remove from the queue
        if t < time.time()-(60*lookBackTime): # if it is older then the lookBackTime in minutes then do nothing and dont re-add to the queue
            continue # skip to next loop itereation
        else: # if time stamp is in the lookBackTime window 
            l.append(t) # add it back to the queue
            sumtime = sumtime + 1 # add one to the sum
            if oldesttime > t: # if t is older then the oldest time
                oldesttime = t - 1 # set the oldest time to one second older then t.
                # this will give me a more accurate average because it took some time to make the first punch

    for e in l: # For every element in l
        eatime.put(e) # put that element back into the queue
    average = (sumtime-1)/((time.time() - oldesttime)/60) # calculate the average takt
    taktval = average
    takt.set("{0:.2f} /min".format(average)) # set the UI label

        
            

# Fire when an operation occurs
def opAction(val):
    global currentOp
    global opmCnt
    global running
    global op
    global opCnt
    global ppmCnt
    global eatime
    
    opmCnt = opmCnt + 1 # add on the the operation per minute array

    currentOp = currentOp + 1 # add one to the current opperation on this part
    op.set(str(currentOp)+"/"+str(opCnt)) # set the Op UI label 
    if(currentOp == opCnt): # if current operations is equal to the number of operations per part
        countUp("cnt") # add one the the item count on screen
        ppmCnt = ppmCnt + 1 # add one to the actual parts array
        eatime.put(time.time()) # Add a time stamp for the current created part.
        calcTakt() # calculat the takt
        currentOp = 0 # reset the current operation to 0 for the next part

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
    global graph
    global runSpeed

    insAct = activityIns
    insProdtakt = prodtaktIns

    global takt
    global op
    global countStr
    global stoptime
    global runtime
    global runningVal
    global stopVal
    global efficiency
    # This is root container 
    root = Tk()
    root.title("Production")

    rowst = 0
    while rowst < 10:
        root.rowconfigure(rowst, weight = 1)
        root.columnconfigure(rowst, weight = 1)
        rowst += 1

    # Set up tabbed navigation

    tabBar = ttk.Notebook(root)
    tabBar.grid(row=1, column=0, columnspan=10, rowspan=49, sticky='NESW')

    monitorTab = ttk.Frame(tabBar)
    graphTab = ttk.Frame(tabBar)
    schedTab = ttk.Frame(tabBar)

    tabBar.add(monitorTab, text="Monitor")
    tabBar.add(graphTab, text="History")
    tabBar.add(schedTab, text="Schedule")

    ########## BEGIN MONITOR TAB #####################################

    # Set base labels for the operator interface.
    takt = StringVar()
    countStr = StringVar()
    runtime = StringVar()
    stoptime = StringVar()
    op = StringVar()
    efficiency = StringVar()

    # Set base labels for the operator interface.
    takt.set("0.0/min")
    countStr.set("0");
    runtime.set("0:00")
    stoptime.set("0:00")
    op.set("0/1")

    # Simple Frames for organizing the widgets
    top = Frame(monitorTab)
    topt = Frame(top)
    topb = Frame(top)
    left = Frame(monitorTab)
    leftl = Frame(left)
    leftr = Frame(left)
    right = Frame(monitorTab)
    
    # Creating Button and label widgets
    up = Button(right, text = "AddCnt", command = lambda:countUp("oi"), width = 15, font = ("Curier", 16))
    down = Button(right, text = "CntDown", command = lambda:countDown("oi"), width = 15, font = ("Curier", 16))
    reset = Button(right, text = "Reset", command = lambda:resetCount("oi"), width = 15, font = ("Curier", 16))
    runningLabel = Label(leftl, text = "Running",relief = RAISED, font= ("Curier", 20),width = 10)
    runningVal = Label(leftr, textvariable = runtime,relief = RAISED,font = ("Curier", 20),width = 10)
    stopLabel = Label(leftl, text = "Stopped",relief = RAISED, font =("Curier", 20),width = 10)
    stopVal = Label(leftr, textvariable = stoptime,relief = RAISED,font = ("Curier", 20),width = 10)
    efficiencyLabel = Label(leftl, text="Efficiency", relief = RAISED, font = ("Curier", 20),width = 10)
    efficiencyVal = Label(leftr, textvariable = efficiency,relief = RAISED,font = ("Curier", 20),width = 10)
    blankl = Label(leftl, text = " ",relief = RAISED, font =("Curier", 20),width = 10)
    blankl2 = Label(right, text = " ",relief = RAISED, font = ("Curier", 16),width = 15)
    totall = Label(leftr, text = "Totals",relief = RAISED, font =("Curier", 20),width = 10)
    taktl = Label(topt, text = "TAKT", relief = RAISED, font =("Curier", 20), width = 10)
    eal = Label(topt, text = "OP/EA", relief = RAISED, font =("Curier", 20), width = 10)
    countl = Label(topt, text = "Count", relief = RAISED, font =("Curier", 20), width = 10)
    taktVal = Label(topb, textvariable = takt, relief = RAISED, font =("Curier", 20), width = 10)
    operationVal = Label(topb, textvariable = op ,relief = RAISED,font = ("Curier", 20), width = 10)
    countVal = Label(topb, textvariable = countStr, relief = RAISED,font = ("Curier", 20), width = 10)

    runningVal.config(bg="gray")
    stopVal.config(bg="gray")

    # Adding Widgets and frames all together
    taktVal.pack(side = LEFT )
    operationVal.pack(side = LEFT)
    countVal.pack(side = LEFT)
    taktl.pack(side = LEFT )
    eal.pack(side = LEFT)
    countl.pack(side = LEFT)
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
    efficiencyLabel.pack()
    efficiencyVal.pack()
    up.pack()
    down.pack()
    reset.pack()
    blankl2.pack()


    ########## END MONITOR TAB    ####################################

    ########## BEGIN HISTORY TAB  ####################################

    global graphFigure

    graphFigure = Figure(figsize=(5,5), dpi=100)
    graph = graphFigure.add_subplot(111)
    graph.xaxis.set_major_formatter(mdate.DateFormatter('%H:%M'))
    graph.xaxis_date()
    canvas = FigureCanvasTkAgg(graphFigure, graphTab)
    canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)

    ########## END HISTORY TAB    ####################################

    ########## BEGIN SCHEDULE TAB ####################################
    
    ########## END SCHEDULE TAB   ####################################

    #TESTING#############################################################
    #testing = Tk()
    #testing.title("Input tester")

    #ACTION_TI = Button(testing, text = "Action", command =lambda:opAction("test"), width = 15, font = ("Curier", 16)).pack()
    #ADD_CNT_TI = Button(testing, text = "Add Cnt", command =lambda:countUp("test"), width = 15, font = ("Curier", 16)).pack()
    #DEC_CNT_TI = Button(testing, text = "Dec Cnt", command =lambda:countDown("test"), width = 15, font = ("Curier", 16)).pack()
    #RESET_CNT_TI = Button(testing, text = "Reset Cnt", command =lambda:reset("test"), width = 15, font = ("Curier", 16)).pack()
    #INC_OP_CNT_TI = Button(testing, text = "Inc Op", command =lambda:incrementOp("test"), width = 15, font = ("Curier", 16)).pack()
    #####################################################################
    
    ani = animation.FuncAnimation(graphFigure,animate,interval=1000)
    
    root.mainloop()
