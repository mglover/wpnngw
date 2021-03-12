#!/usr/bin/env python3
"""
addgroup.py
"""
import sys, os, json, subprocess
from wpnngw.util import fatal, inn_config
from wpnngw.gwgroup import GatewayedGroup


def add_newsgroup(group):
	active = os.path.join(inn_config()['pathdb'], 'active')
	cmd = 'newgroup'
	for l in open(active).readlines():
		name, _, _, status = l.split()
		if name != group: continue
		if status == 'm':
			print("newsgroup %s exists" % group)
			return   #group exists and is moderated, nothing to do
		cmd = 'changegroup'
	ret = subprocess.run(['ctlinnd', cmd, group, 'm'])
	if ret.returncode != 0:
		fatal("ctlinnd failed with return code %d" % ret.returncode)


def add_group_files(group, site):
	grp = GatewayedGroup(group)
	if grp.exists():
		print("group directory %s exists" % grp.dir())
	grp.create()

	d = {
		'source': site,
		'group': group,
		'posts': {},
		'updated': "1970-01-01T00:00:00-00"
	}
	history = os.path.join(grp.dir(), 'history.json')
	with open(history, 'w') as f:
		json.dump(d, f, indent=2)


if __name__ == '__main__':
	me = os.path.basename(sys.argv[0])

	if len(sys.argv) < 3: fatal("usage: %s group site" % me)
	group, site = sys.argv[1:3]
	add_group_files(group, site)
	add_newsgroup(group)

	moderators = os.path.join(inn_config()['pathetc'], 'moderators')
	print("add the following line to the top of %s'" % moderators)
	print("%s:%%s@wpnngw.local" % group)

