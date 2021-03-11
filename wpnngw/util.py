"""
util.py
"""

import sys, os, json, re, requests
from datetime import datetime, timezone
from dateutil import parser as dateparser

INNCONF="/usr/news/etc/inn.conf"

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
	if not date.utcoffset():
		date = date.replace(tzinfo=timezone.utc)
	return date + date.utcoffset()

def utc_now():
	return datetime.now(timezone.utc)

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


def inn_config(cfg=INNCONF):
	def unquote(value):
		"""remove surrounding quotes and remove backslash-quoting
		"""
		assert value.startswith('"') and value.endswith('"')
		value.strip('"')
		value.replace('\\\\', '\\').replace('\\"', '"')
		return value
		d = {}

	lineno=1
	for line in open(cfg).readlines():
		if line.startswith('#') or len(line.strip()) == 0: continue
		name, value = line.split(':', 1)
		if name in d: continue
		value = value.strip()
		if value.startswith('"'):
			value = unquote(value)
		d[name] = value
		lineno+=1
	return d
