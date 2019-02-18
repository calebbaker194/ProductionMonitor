import psycopg2
from uuid import getnode as get_mac
import tkinter as tk
lookBackTime = 0
lookBackDist = 0
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
    def enterName(rwin,name,time,dist):
        global pittsteel
        global lookBackTime
        global lookBackDist
        cur.execute("""INSERT INTO psproductivity.station (station_name,station_mac,station_lbt,station_lbd) VALUES(%s,%s,%s,%s)""",(name,mac,time,dist))
        pittsteel.commit()
        cur.execute("""SELECT station_lbt,station_lbd FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        rows2 = cur.fetchall()
        lookBackTime = rows2[0][0]
        lookBackDist = rows2[0][1]
        nonlocal callmain
        rwin.destroy()
        setStationId(-1,callmain)
        

    if(len(rows) == 0):
        question = tk.Tk()
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
        cur.execute("""SELECT station_lbt,station_lbd FROM psproductivity.station WHERE station_mac = %s;""",(mac,))
        global lookBackTime
        global lookBackDist
        rows2 = cur.fetchall()
        lookBackTime = rows2[0][0]
        lookBackDist = rows2[0][1]
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

def getSched(treeview):
    global station_id
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

def updateWork(woitem_id, qty):
    global station_id
    print("Thanks for the update")
