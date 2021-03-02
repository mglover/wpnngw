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

def rfc_date(datestr):
	date = dateparser.parse(datestr)
	return datetime.strftime(date, "%d %b %Y %H:%M:%S %z")

def iso_datetime(datestr):
	""" Wordpress API requires a two-digit timezone specifier ???"""
	date = dateparser.parse(datestr)
	return datetime.strftime(date, '%Y-%m-%dT%H:%M:%S-00')

known_authors = {}
def author_from_id(site, id):
	if id not in known_authors:
		resp=requests.get(site+'/wp-json/wp/v2/users/'+str(id))
		known_authors[id] = json.loads(resp.text)['name']
	return known_authors[id]

def maybe_wrap(para):
	"""wrap paragraphs that are not primarily URLs
	"""
	s=e=para.find('http')
	if e != -1:
		while e<len(para) and not para[e].isspace(): e+=1
		if e-s > len(para)/2: return para
	return '\n'.join(textwrap.wrap(para))

def unwrap(text):
	"""remove all 'wrapping' newlines, but preserve '\n\n' sequences
	"""
	return re.sub('[^\n]\n[^\n]', '', text)

def groupsdir():
	"""return the path to the directory containing gatewayed group dirs
	"""
	dir = os.environ.get('WPNNGW_HOME')
	if not dir: 
		home = os.environ.get('HOME')
		if not home: raise ValueError('no WPNNGW_HOME, nor HOME')
		dir = os.path.join(home, 'wpnngw_groups')
	return dir
