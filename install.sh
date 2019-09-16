
sudo apt-get update
sudo apt-get install mariadb-server libmariadbclient-dev
#fix submodule remotes
git submodule sync
git submodule update --init --recursive

pipenv install

# #############################
# # Drop and install database
# #############################
# create random password
# PASSWDDB="$(openssl rand -base64 12)"
read -p "Drop and install database [Y/n]: " response
if [ "" = "$response" ] || [ "Y" = "$response" ] || [ "y" = "$response" ]; then
    PASSWDDB="21oFw7Yevum5"

    # replace "-" with "_" for database username
    MAINDB="automation_scripts"

    DBUSER='automation_user'

    sudo mysql -uroot -e "DROP DATABASE ${MAINDB};"
    sudo mysql -uroot -e "DROP USER ${DBUSER}@localhost;"
    sudo mysql -uroot -e "CREATE DATABASE ${MAINDB} /*\!40100 DEFAULT CHARACTER SET utf8 */;"
    sudo mysql -uroot -e "CREATE USER ${DBUSER}@localhost;"
    sudo mysql -uroot -e "GRANT ALL ON automation_scripts.* TO 'automation_user'@'localhost' IDENTIFIED BY '21oFw7Yevum5';"
    sudo mysql -uroot -e "FLUSH PRIVILEGES;"
# create database automation_scripts;
# create user automation_user;
# grant all on automation_scripts.* to 'automation_user'@'localhost' identified by '21oFw7Yevum5';
fi

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








# #create or copy config.ini
# vim config.ini 

# python RegistrationMonitor.py 

# pipenv shell
# pipenv install


echo "Done!"