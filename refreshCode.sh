#!/bin/bash

xhost +
cd /home/pi/src/ProductionMonitor
git pull
cp /home/pi/src/ProductionMonitor/* /home/pi/Desktop/Production
cd /home/pi/Desktop/Production
cp /home/pi/Desktop/Production/refreshCode.sh /home/pi/Desktop/
sudo ./getupdates.sh
/usr/bin/python3 prodmain.py 2>&1 >> logfile.data
