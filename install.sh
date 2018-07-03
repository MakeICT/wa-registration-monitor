# sudo raspi-config
#     #set locale and timezone
# sudo apt-get update && sudo apt-get upgrade
# sudo apt-get install mysql-server python3-dateutils python3-mysqldb python3-apscheduler python3-pip
# sudo pip3 install smartwaiver-sdk meetup-api
# mkdir code
# cd code
# sudo apt-get install git
# git clone https://github.com/MakeICT/automation-scripts.git
# cd automation-scripts/
# #pull submodules

# #############################
# # Drop and install database
# #############################
# create database automation_scripts;
# create user automation_user;
# grant all on automation_scripts.* to 'automation_user'@'localhost' identified by '21oFw7Yevum5';

#############################
# Enable service
#############################
read -p "Install and enable service [Y/n]: " response
if [ "" = "$response" ] || [ "Y" = "$response" ] || [ "y" = "$response" ]; then
    f=automation-scripts.service
    sudo systemctl disable 'automation-scripts' > /dev/null 2>&1
    echo "
        [Unit]
        Description=Automation Scripts
        
        [Service]
        ExecStart=`which python3` `pwd`/Dispatcher.py
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
    echo "        sudo python3 ./Dispatcher.py"
fi
echo "Done!"