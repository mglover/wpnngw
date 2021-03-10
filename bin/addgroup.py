#!/usr/bin/env python3
"""
addgroup.py
"""
import sys, os, json
from wpnngw.util import groupsdir, fatal

def add_group(group, site):
	dir = groupsdir()
	groupdir = os.path.join(dir, group)

	if not os.path.isdir(groupdir): os.mkdir(groupdir)
	for subdir in ('incoming', 'active', 'processed'):
		sp = os.path.join(groupdir, subdir)
		if not os.path.isdir(sp): os.mkdir(sp)

	d = {
		'source': site,
		'group': group,
		'posts': {},
		'updated': "1970-01-01T00:00:00"
	}
	history = os.path.join(groupdir, 'history.json')
	with open(history, 'w') as f:
		json.dump(d, f, indent=2)


if __name__ == '__main__':
	me = os.path.basename(sys.argv[0])
	if len(sys.argv) < 3: fatal("usage: %s group site" % me)
	add_group(sys.argv[1], sys.argv[2])
