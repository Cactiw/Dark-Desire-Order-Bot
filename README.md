# Dark-Desire-Order-Bot

Source code for Telegram bots @DarkDesireCastleBot and @Rock_Centre_Order_bot.

Related files to castle bot are located in directory castle_files, while order files ale located in order_files.

castle_bot.py and order_bot.py are main files to the both bots. You can run them separately, but be aware of 
queue`s overthlow. 


## Installation
`sudo apt-get update`

`sudo apt-get install python3-pip python3-setuptools postgresql postgresql-contrib vim`

`cd /etc/postgresql/10/main`
(10 is version number, replace for your one)

`vim pg_hba.conf`




    Open the file pg_hba.conf for Ubuntu it will be in /etc/postgresql/9.x/main and change this line:

    local   all             postgres                                peer

    to

    local   all             postgres                                trust

Restart the server

  `sudo service postgresql restart`

Login into psql and set your password

`psql -U postgres`

`ALTER USER postgres with password 'your-pass';`

    Finally change the pg_hba.conf from

    local   all             postgres                                trust

    to

    local   all             postgres                                md5
`sudo su - posgtres`

`createuser --interactive -P admin --pwprompt`

`createdb admin admin`

`logout`

`psql -U admin`

`create database darkdesirecastlebot;`

`sudo timedatectl set-timezone Europe/Moscow`
(To set server timezone to Moscow)

`git clone https://github.com/Cactiw/Dark-Desire-Order-Bot.git`

`cd Dark-Desire-Order-Bot`

`sudo pip3 install -r requirements.txt`

And create config.py file like this:

```python3
psql_creditals = {'dbname': 'darkdesirecastlebot', 'user': 'admin', 'pass': 'your pass'}
Production_order_token = 'Order token'
Production_castle_token = 'Castle token'

ServerIP = 'Your ip'

CONNECT_TYPE = 'long_pooling'  # or 'webhook'
request_kwargs = {'proxy_url': 'proxy url'}  # or None if no proxy is needed

# For telethon functions
phone = 'Your phone'
username = 'Your telegram username'
password = ''  # if you have two-step verification enabled

api_id = Telegram API_ID
api_hash = "Telegram API HASH"

cwuser = "CW3 API username"
cwpass = "CW3 API password"


```
