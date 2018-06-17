#!/usr/bin/python3

# Robert Cudmore
# 20180613
#
# requires python 3.x
#
# usage:
#	python3 startuptweet.py "my tweet"

import os, sys, socket, subprocess, json
from uuid import getnode as get_mac
from datetime import datetime
import tweepy

message = ''
if len( sys.argv ) > 1:
    message = ' ' + sys.argv[1] + ' '

# Create variables for each key, secret, token
# Change to your own account information to send from
if os.path.isfile('twitter_auth.secret.json'):
	with open('twitter_auth.secret.json') as f:
		twitter_auth = json.load(f)
else:
	print("ERROR: did not find twitter_auth.secret.json file -->> exiting")
	sys.exit()

# Set up OAuth and integrate with API
auth = tweepy.OAuthHandler(twitter_auth['consumer_key'], twitter_auth['consumer_secret'])
auth.set_access_token(twitter_auth['access_token'], twitter_auth['access_token_secret'])
api = tweepy.API(auth)

thetime = datetime.now().strftime('%Y%m%d %H:%M:%S')

ip = subprocess.check_output(['hostname', '--all-ip-addresses'])
ip = ip.decode('utf-8').strip()

hostname = socket.gethostname()

mac = get_mac()
mac = hex(mac)

tweet = hostname + message + thetime + ' ' + ip + ' ' + mac + ' ' + '#homecageswarm'

try:
	api.update_status(status=tweet)
except:
	print('exception in api.update_status')
	raise