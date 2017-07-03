#!/bin/bash

sudo apt-get install python3-dateutil 
sudo apt-get install python3-mysqldb
sudo apt-get install mysql-server 

sudo mysql
CREATE USER 'regimon'@'localhost' IDENTIFIED BY 'regimon';
CREATE DATABASE regimon_db;
GRANT ALL PRIVILEGES ON regimon_db . * TO 'regimon'@'localhost';

#############################
# Enable service
#############################
read -p "Install and enable service [Y/n]: " response
if [ "" = "$response" ] || [ "Y" = "$response" ] || [ "y" = "$response" ]; then
	f=registration-monitor.service
	sudo systemctl disable 'registration-monitor' > /dev/null 2>&1
	echo "
		[Unit]
		Description=WildApricot Registration Monitor
		
		[Service]
		ExecStart=`which python3` `pwd`/RegiMon.py
		WorkingDirectory=`pwd`
		Restart=always
		[Install]
		WantedBy=multi-user.target
	" | awk '{$1=$1};1' > $f

	sudo systemctl enable `pwd`/$f
	echo ""
	echo "    To start the service, use"
	echo "        sudo systemctl start $f"
	echo "    or reboot"
	echo "    To run manually, use"
	echo "        sudo python3 ./RegiMon.py"
fi
echo "Done!"