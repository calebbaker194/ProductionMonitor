#!/bin/bash

cd ~/src/ProductionMonitor
sudo git pull
sudo cp ~/src/ProductionMonitor/* ~/Desktop/Production
cd ~/Desktop/Production
sudo python3 prodmain.py > logfile.data
