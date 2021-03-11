"""
util.py
"""

import sys, os, json, re, requests
from datetime import datetime, timezone
from dateutil import parser as dateparser

INNCONF="/usr/local/news/etc/inn.conf"

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


class QueueDir(object):
	""" A failure-safe queue of files to process
		(based on DJB's mechanism in qmail)
		unprocessed files are written to root/new
		moved to root/cur while being processed
		and moved to root/fin on success
		files with processing failures will be left in root/new
	"""
	def __init__(self, root):
		self.root = root
		self.new = os.path.join(root, 'new')
		self.cur = os.path.join(root, 'cur')
		self.fin = os.path.join(root, 'fin')

	def _mkdirs(self):
		if not os.path.isdir(self.root):
			os.mkdir(self.root)
		for sub in [self.new, self.cur, self.fin]:
			if not os.path.isdir(sub):
				os.mkdir(sub)

	def newfile(self, filename):
		self._mkdirs()
		path = os.path.join(self.new, filename)
		if os.path.exists(path): raise ValueError("File exists: %s" % path)
		return path

	def process(self, proc):
		self._mkdirs()
		for f in os.listdir(self.new):
			n = os.path.join(self.new, f)
			c = os.path.join(self.cur, f)
			f = os.path.join(self.fin, f)
			os.rename(n, c)
			if proc(c):
				os.rename(c, f)

	def pending(self):
		"""return the full paths of all unprocessed files
		"""
		return [os.path.join(self.new, f) for f in os.listdir(self.new)]

	def errors(self):
		"""return the full paths of all files that had processing errors
		"""
		return [os.path.join(self.cur, f) for f in os.listdir(self.cur)]
