# ProductionMonitor

This is the source for the production monitor code. Its broken into 2 different file types, Shells and python Sripts.

#   Shell   #
There are 3 Shell Files

getupdates.sh
initStart.sh
refreshCode.sh

getupdates.sh - will be used to preform shell updates on the pi. If you add new code that needs an external library you can add somthing in the getupdates.sh to install a package through something like pip or apt-get. 

initStart.sh - This is used as the code to run for the inital start of the raspberry pi. At the time of its runnning all of the dependencis are covered in the initStart Script. 

refreshCode.sh - This is the run script for the production monitor. It will pull the latest python code from github and move it to the launch directory. It then runs the getupdates.sh script to install any new dependencies. After it has installed all of the dependencies it will run the up to date python code.

#   Python   #
There are 3 Python Files

dsplay.py
pgdriv.py
prodmain.py

prodmain.py - This is the entry point for the production monitor code. It does some inital setup as well as creates a timer thread to keep the programs "clock speed" once inital setup is done it will launch the gui contained in dsplay.

pgdrive.py - This file is the bulk of the database work. If any communication to the database occures then this file will handle it. it also handles most of the startup recovery logic.

dsplay.py - this is the bulk of the running program. It contains the setup of the gui program as well as the logic for the Raspberry Pi's GPIO. Most of the program logic happens here and most bugs will be in this code.

#   Notes   #

In the main source directory, There is a folder called RPi. This allows you to run the program on a computer that does not have any GPIO. If you get to a point where you get an error stating that RPi.GPIO does not contain... Then simply add the method or constant that you are trying to use into the RPi/GPIO.py File and it will remove these errors. For obvious reasons, this "simulated" GPIO is not functional as there is no hardware for you to use. You should not have this inside of the ~/Desktop/Production Folder of your Raspberry Pi.
