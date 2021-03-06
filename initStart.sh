#!/bin/bash
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install git
mkdir ~/Desktop/Production
mkdir ~/src
cd ~/src
git clone https://github.com/calebbaker194/ProductionMonitor
cd ./ProductionMonitor
git pull
cp ./* ~/Desktop/Production/
cp ./refreshCode.sh ~/Desktop
sudo apt-get -y install 
sudo pip3 install psycopg2-binary
sudo pip3 install pyautogui
sudo pip3 install Xlib
sudo pip3 install -U matplotlib
echo "deb-src http://apt.postgresql.org/pub/repos/apt/ wheezy-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install build-essential fakeroot
sudo apt-get -y build-dep postgresql-9.4
sudo apt-get -y build-dep postgresql-common
sudo apt-get -y build-dep postgresql-client-common
sudo apt-get -y build-dep pgdg-keyring
sudo apt-get -y install matchbox-keyboard
sudo apt-get -y install libpq-dev
echo "@/home/pi/Desktop/refreshCode.sh" >> /home/pi/.config/lxsession/LXDE-pi/autostart
reboot
