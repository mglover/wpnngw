"""
util.py
"""

import os, json, re, requests, textwrap
from datetime import datetime
from dateutil import parser as dateparser

print_debugging = False

def fatal(msg):
	sys.stderr.write(msg+'\n')
	sys.exit(1)

def debug(*args):
	if print_debugging: print(*args)

def utc_datetime(datestr):
	""" take a random-format datetime string and return
	    a UTC datetime object
		(troublingly, assume UTC in the absence of timezone data)
	"""
	date = dateparser.parse(datestr)
	if not date.utcoffset(): return date
	return date + date.utcoffset()

def rfc_datestr(utc_date):
	""" take a UTC datetime object and return and RFC-formatted string
	"""
	return datetime.strftime(utc_date, "%d %b %Y %H:%M:%S -0000")

def iso_datestr(utc_date):
	""" take a UTC datetime object and return an ISO-formatted string
		(with the two-digit timezone specifier required() by WP API)
	"""
	return datetime.strftime(utc_date, '%Y-%m-%dT%H:%M:%S-00')
	#datetime.strftime(date_utc, "%Y-%m-%dT%H:%M:%SZ"),

def groupsdir():
	"""return the path to the directory containing gatewayed group dirs
	"""
	dir = os.environ.get('WPNNGW_HOME')
	if not dir: 
		home = os.environ.get('HOME')
		if not home: raise ValueError('no WPNNGW_HOME, nor HOME')
		dir = os.path.join(home, 'wpnngw_groups')
	return dir
