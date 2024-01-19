#!/bin/bash
# Generate new passwords
DB_USER_PASS=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 24 ; echo '')
DB_ROOT_PASS=$(tr -dc A-Za-z0-9 </dev/urandom | head -c 24 ; echo '')

# Modify the .env file
sed -i "s/MYSQL_PASSWORD=.*$/MYSQL_PASSWORD=$DB_USER_PASS/g" .env
sed -i "s/MYSQL_ROOT_PASSWORD=.*$/MYSQL_ROOT_PASSWORD=$DB_ROOT_PASS/g" .env

# Copy it inside the docker folder
ln -fP .env curl_bible/
ln -fP .env bible_db/
echo -e "\e[32mFiles successfully modified!\e[0m"
echo -e "Regular DB user password is: \e[1m$DB_USER_PASS\e[0m\nRoot DB user password is:    \e[1m$DB_ROOT_PASS\e[0m"