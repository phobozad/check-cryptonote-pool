#!/usr/bin/env python

import requests
import sys
import argparse

# Argument Parsing
parser = argparse.ArgumentParser(description="Query a cryptonote-universal-pool mining pool API to get current mining hashrate for a given payment address.")
parser.add_argument("-w", metavar="HASHRATE", type=int, dest="warnThresh", help="Warning threshold", required=True)
parser.add_argument("-c", metavar="HASHRATE", type=int, dest="critThresh", help="Critical threshold", required=True)
parser.add_argument("-a", metavar="ADDRESS", dest="payAddress", help="Payment address to query on", required=True)
parser.add_argument("-u", metavar="URL", dest="url", help="URL to pool's API (include port)", required=True)

args = parser.parse_args()

# Verify parameters passed in

warnThresh = args.warnThresh
critThresh = args.critThresh
payAddress = args.payAddress
url = args.url.rstrip("/") + "/stats_address"

if warnThresh < critThresh:
	print "Error: Warning threshold must be greater than critical threshold"
	sys.exit(3)


# Variables
exitCode=3
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}

urlParams = dict (
	address=payAddress,
	longpoll="false"
)


def prefixToMultiplier(prefix):
	prefix=prefix.strip().lower()
	# Note that cryptonote-universal-pool's API mis-calculates when it scales the hashrate
	# We mirror that miscalculation (using 1024 instead of 1000) here to get the true hashrate in H/s
	# This conversion is in /lib/api.js in the cryptonote-universal-pool source code
	switcher = {
		"h":	1,
		"kh":	1024,
		"mh":	1024 ** 2,
		"gh":	1024 ** 3,
		"th":	1024 ** 4,
		"ph":	1024 ** 5
	}
	return switcher.get(prefix, 0)


# Get the data & parse it

response = requests.get(url=url, params=urlParams)

if response.status_code == requests.codes.ok:
	data = response.json()

	try:
		data = data["stats"]["hashrate"].split()
	except KeyError:
		# when the hashrate is zero, API doesn't return a hashrate item
		data = "0.00 H"
		data = data["stats"]["hashrate"].split()
	
	hashRate = float(data[0]) * prefixToMultiplier(data[1])
	if hashRate < critThresh:
		exitCode=2
		output="Critical - Hash rate: {} {}/s".format(data[0],data[1])
	elif hashRate < warnThresh:
		exitCode=1
		output="Warning - Hash rate: {} {}/s".format(data[0],data[1])
	else:
		exitCode=0
		output="OK - Hash rate: {} {}/s".format(data[0],data[1])

	output += " | Hashrate={};{};{};;".format(hashRate, warnThresh, critThresh)
	print output
else:
	exitCode=3
	print "HTTP Error: {}".format(response.status_code)

sys.exit(exitCode)
