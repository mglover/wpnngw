#!/usr/bin/env python3
"""
addgroup.py
"""
import sys, os, json
from wpnngw.util import fatal
from wpnngw.gwgroup import GatewayedGroup


def add_group(group, site):
	grp = GatewayedGroup(group)
	if grp.exists:
		fatal("group %s exists")
	grp.create()

	d = {
		'source': site,
		'group': group,
		'posts': {},
		'updated': "1970-01-01T00:00:00"
	}
	history = os.path.join(grp.dir(), 'history.json')
	with open(history, 'w') as f:
		json.dump(d, f, indent=2)


if __name__ == '__main__':
	me = os.path.basename(sys.argv[0])
	if len(sys.argv) < 3: fatal("usage: %s group site" % me)
	add_group(sys.argv[1], sys.argv[2])
