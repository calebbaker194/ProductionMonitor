import psycopg2
from uuid import getnode as get_mac
from datetime import datetime
import tkinter as tk
import time
import socket
import logging
from collections import deque

sqlQueue = deque()

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255',1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

logging.basicConfig(filename='pgdrive.log', level=logging.DEBUG, format='[%(asctime)s]: %(message)s')
ACTION_di = 17
ADD_CNT_di = 5
DEC_CNT_di = 27
RESET_CNT_di = 18
INC_OP_CNT_di = 12
LBT = 0
station_name = ""
LBD = 0
mac = get_mac()
station_id_set = True
passing = False
# The id for the current running record
activity_id = -1;
print('starting drive')
timeouttime = time.time()
while not passing:
    try:
        pittsteel = psycopg2.connect(database='PittSteel',
                                     host='192.168.2.6',
                                     user='prodmon',
                                     password='prodmonpass',
                                     port=5432,
                                     connect_timeout=3,
                                     keepalives=1,
                                     keepalives_idle=5,
                                     keepalives_interval=2,
                                     keepalives_count=3,)
        cur = pittsteel.cursor()
        passing=True
    except Exception as e:
        if time.time() - timeouttime > (10):
            passing=True

station_id = -1

def isConnected():
    global pittsteel
    global cur

    if len(sqlQueue) != 0:
        print('true')
        return True
    try:
        cur.execute('SELECT 1')
        print('true')
        return True
    except Exception as e:
        print(e)
        print('false')
        return False

def emptyQueue():
    global pittsteel
    global cur
    global station_id_set
    global station_id
    global sqlQueue

    if len(sqlQueue) == 0:
        return

    try:
        pittsteel = psycopg2.connect(database='PittSteel',
                                     host='192.168.2.6',
                                     user='prodmon',
                                     password='prodmonpass',
                                     port=5432,
                                     connect_timeout=3,
                                     keepalives=1,
                                     keepalives_idle=5,
                                     keepalives_interval=2,
                                     keepalives_count=3,)
        cur = pittsteel.cursor()
        if not station_id_set:
            cur.execute("""SELECT station_id,station_name FROM psproductivity.station WHERE station_mac = %s;""",
                        (mac,))
            rows = cur.fetchall()
            station_id = rows[0][0]
        while sqlQueue:
            instruct = sqlQueue.popleft()
            try:
                if instruct['function'] == 'start':
                    start(instruct['time'])
                elif instruct['function'] == 'stop':
                    stop(instruct['time'])
                elif instruct['function'] == 'insertprodtakt':
                    insertprodtakt(instruct['takt'],instruct['time'])
            except Exception as e:
                print(e)
                sqlQueue.appendleft(instruct)


    except Exception as e:
        print(e)
        print('Empty Queue Failed')
        passing = False


def setStationId(station,callmain):
    global station_id
    try:
        station_id = station
        if station_id == -1:
            try:
                cur.execute("""SELECT station_id,station_name FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
                rows = cur.fetchall()
                station_id = rows[0][0]
            except:
                global station_id_set
                station_id_set = False
        callmain()
    except Exception as e:
        print("Set Station id failed: "+e.message)

def getLastPiece():
    global station_id
    try:
        cur.execute("""SELECT prodtakt_start FROM psproductivity.prodtakt WHERE prodtakt_station_id = %s ORDER BY prodtakt_start DESC LIMIT 1""",(station_id,))
        rows = cur.fetchall()
        return rows[0][0].timestamp()
    except Exception as e:
        return -1


def loadPreviousOrDefault():
    global LBT
    global LBD
    global ACTION_di
    global ADD_CNT_di
    global DEC_CNT_di
    global RESET_CNT_di
    global INC_OP_CNT_di

    ACTION_di = 17
    ADD_CNT_di = 5
    DEC_CNT_di = 27
    RESET_CNT_di = 18
    INC_OP_CNT_di = 12
    LBT = 5
    LBD = 2


def register(callmain):
    global mac
    global cur
    try:
        cur.execute("""SELECT station_id,station_name FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        rows = cur.fetchall()
        def enterName(rwin,name,time,dist):
            global pittsteel
            global LBT
            global LBD
            cur.execute("""INSERT INTO psproductivity.station (station_name,station_mac,station_lbt,station_lbd,action,addcnt,deccnt,resetcnt,incop,station_ip_addr) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(name,mac,time,dist,17,5,27,18,12,get_ip()))
            pittsteel.commit()
            cur.execute("""SELECT station_lbt,station_lbd FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
            rows2 = cur.fetchall()
            LBT = rows2[0][0]
            LBD = rows2[0][1]
            nonlocal callmain
            rwin.destroy()
            setStationId(-1,callmain)


        if(len(rows) == 0):
            question = tk.Tk()
            question.title("Configure")
            tk.Label(question, text = 'Enter Station Name').pack()
            a = tk.Entry(question)
            a.pack()
            tk.Label(question, text = 'Enter Look Back Time').pack()
            b = tk.Entry(question)
            b.pack()
            tk.Label(question, text = 'Enter Look Back Operations').pack()
            c = tk.Entry(question)
            c.pack()
            tk.Button(question, text='Submit', command = lambda:enterName(question,a.get(),b.get(),c.get())).pack()
            question.mainloop()
        else :
            global station_name
            station_name = rows[0][1]
            cur.execute("""SELECT station_lbt,station_lbd,action,addcnt,deccnt,resetcnt,incop FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
            global LBT
            global LBD
            global ACTION_di
            global ADD_CNT_di
            global DEC_CNT_di
            global RESET_CNT_di
            global INC_OP_CNT_di

            rows2 = cur.fetchall()
            ACTION_di = rows2[0][2]
            ADD_CNT_di = rows2[0][3]
            DEC_CNT_di = rows2[0][4]
            RESET_CNT_di = rows2[0][5]
            INC_OP_CNT_di = rows2[0][6]
            LBT = rows2[0][0]
            LBD = rows2[0][1]
            cur.execute("""UPDATE psproductivity.station SET station_ip_addr = %s WHERE station_id = %s""",(get_ip(),rows[0][0]))
            pittsteel.commit()
            setStationId(rows[0][0],callmain)
    except:
        loadPreviousOrDefault()
        setStationId(-1,callmain)


def start(actTime):
    global station_id
    global sqlQueue
    global pittsteel
    global activity_id
    try:
        cur.execute("""SELECT nextVal('psproductivity.activity_activity_id_seq') AS result""")
        row = cur.fetchall()
        activity_id = row[0][0]
        cur.execute("""INSERT INTO psproductivity.activity (activity_id,activity_start_time,activity_station_id) VALUES(%s,to_timestamp(%s), %s)""",(activity_id, actTime ,station_id))
        pittsteel.commit()
    except Exception as e:
        print(e)
        print("Start Queued")
        sqlQueue.append({"function" : 'start' , "time" : actTime})
        activity_id = -1;


def stop(actTime):
    global station_id
    global pittsteel
    global activity_id
    try:
        if(activity_id == -1):
            print("Cannot Set stop time when no activity has been set.")
        cur.execute("""UPDATE psproductivity.activity SET activity_stop_time = to_timestamp(%s) WHERE activity_id = %s""",(actTime, activity_id))
        pittsteel.commit()
        activity_id = -1;
    except Exception as e:
        print(e)
        print("Setting Stop Queued")
        sqlQueue.append({"function": 'stop', "time": actTime})
def insertprodtakt(takt, takttime):
    try:
        global station_id
        global pittsteel
    
        cur.execute("""INSERT INTO psproductivity.prodtakt (prodtakt_start,prodtakt_takt,prodtakt_station_id) VALUES(to_timestamp(%s), %s, %s)""",(takttime,takt,station_id))
        pittsteel.commit()

    except Exception as e:
        print("Insert Prodtakt queued: ")
        sqlQueue.append({"function": 'insertprodtakt', "takt" : takt ,"time": takttime})

def getSched(treeview):
    global station_id
    try:
        cur.execute("""
        SELECT pswosched_id, wo_number, item_descrip1, pswosched_submit || '/' || pswosched_request
        FROM psproductivity.pswosched
        JOIN wo ON(wo_id = pswosched_woitem_id)
        JOIN itemsite ON (wo_itemsite_id = itemsite_id)
        JOIN item ON (itemsite_item_id = item_id)
        WHERE pswosched_station_id = %s
        ORDER BY pswosched_priority
        """,(station_id,))

        for row in cur:
            treeview.insert('', 'end', iid=row[0], values=(row[1], row[2], row[3]))
    except Exception as e:
        return

def updateWork(woitem_id, qty):
    global station_id
    

def launchConfig(lastRecord):
    try:
        cur.execute("""
        SELECT activity_start_time,activity_stop_time FROM psproductivity.activity
        WHERE activity_station_id = %s ORDER BY activity_start_time DESC LIMIT 1""",(station_id,))
        rrunning = False
        rStartTime = 0
        global activity_id

        if cur.rowcount == 0:
            return rrunning, rStartTime;

        for row in cur:
            activity_id, ttime = lastRecord()
            if(activity_id != -1):
                activity_id,ttime  = lastRecord()
                if(time.time() - ttime < LBT * 60): # It hasnt been too long just pick up the last running time and set it to running
                    rrunning =True
                    rStartTime = row[1]
                else:
                    stop(ttime) # Otherwise give us a nice stop for the last time it was runnning
            break

        return rrunning, rStartTime
    except:
        return False,False
