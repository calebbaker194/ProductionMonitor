import psycopg2
from uuid import getnode as get_mac
import tkinter as tk
slowSpeed = 0
runSpeed = 0
mac = get_mac()
pittsteel = psycopg2.connect("dbname=PittSteel host=192.168.2.3 user=caleb password=tori")

cur = pittsteel.cursor()
station_id = -1
 
def setStationId(station,callmain):
    global station_id
    station_id = station
    if station_id == -1:
        cur.execute("""SELECT station_id,station_name FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        rows = cur.fetchall()
        station_id = rows[0][0]
        
    callmain()

def register(callmain):
    global mac
    global cur
    
    cur.execute("""SELECT station_id,station_name FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
    rows = cur.fetchall()
    def enterName(rwin,name,fast,slow):
        global pittsteel
        global slowSpeed
        global runSpeed
        cur.execute("""INSERT INTO psproductivity.station (station_name,station_mac,station_slow_speed,station_run_speed) VALUES(%s,%s,%s,%s)""",(name,mac,slow,fast))
        pittsteel.commit()
        cur.execute("""SELECT station_slow_speed,station_run_speed FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        rows2 = cur.fetchall()
        slowSpeed = rows2[0][0]
        runSpeed = rows2[0][1]
        nonlocal callmain
        rwin.destroy()
        setStationId(-1,callmain)
        

    if(len(rows) == 0):
        question = tk.Tk()
        tk.Label(question, text = 'Enter Station Name').pack()
        a = tk.Entry(question)
        a.pack()
        tk.Label(question, text = 'Enter Run Speed').pack()
        b = tk.Entry(question)
        b.pack()
        tk.Label(question, text = 'Enter Slow Speed').pack()
        c = tk.Entry(question)
        c.pack()
        tk.Button(question, text='Submit', command = lambda:enterName(question,a.get(),b.get(),c.get())).pack()
        question.mainloop()
    else :
        cur.execute("""SELECT station_slow_speed,station_run_speed FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        global slowSpeed
        global runSpeed
        rows2 = cur.fetchall()
        slowSpeed = rows2[0][0]
        runSpeed = rows2[0][1]
        setStationId(rows[0][0],callmain)


def insertActivity(actType, actTime):
    global station_id
    global pittsteel
    print("Activity "+actType)
    cur.execute("""INSERT INTO psproductivity.activity (activity_type,activity_time,activity_station_id) VALUES(%s,to_timestamp(%s), %s)""",(actType, actTime ,station_id))
    pittsteel.commit()

def insertprodtakt(takt, takttime):
    global station_id
    global pittsteel
    print("Takt ",takt)
    cur.execute("""INSERT INTO psproductivity.prodtakt (prodtakt_start,prodtakt_takt,prodtakt_station_id) VALUES(to_timestamp(%s), %s, %s)""",(takttime,takt,station_id))
    pittsteel.commit()

