#!/bin/bash

cd /home/pi/src/ProductionMonitor
sudo git pull
sudo cp /home/pi/src/ProductionMonitor/* /home/pi/Desktop/Production
cd /home/pi/Desktop/Production
sudo /usr/bin/python3 prodmain.py >> logfile.data
