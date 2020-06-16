# config.py file example

psql_creditals = {'dbname': 'database_name', 'user': 'username', 'pass': 'password'}

Production_order_token = 'Order token here'
Production_castle_token = 'Castle token here'

ServerIP = 'Server ip here'  # For webhook only, currently not used

# CONNECT_TYPE = 'webhook'
CONNECT_TYPE = 'long_pooling'


# request_kwargs = {'proxy_url': 'socks5h://163.172.152.192:1080'}    #Configured proxy - uncomment if ypu need proxy
# proxy = 'socks5://163.172.152.192:1080'  # This is public python-telegram-bot proxy
# telethon_proxy = {"host": "host", "port": 8443, "secret": "secret_key"}  # Uncomment if you need telethon proxy
proxy = None
request_kwargs = None


# Telethon settings - for stats parse
phone = ''
username = ''
password = ''  # if you have two-step verification enabled

api_id = 17349
api_hash = "344583e45741c457fe1862106095a5eb"


cwuser = "CW API username"
cwpass = "CW API password"

enable_api = False  # Flag to enable CW API connection
enable_telethon = False  # Flag to enable all telethon functions
