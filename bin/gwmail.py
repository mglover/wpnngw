#!/usr/bin/env python3
""" gwmail.py
	intercept mail for WordPress-gatewayed groups
	and post those articles through the blog's approval system
"""

import os, sys, subprocess
from datetime import datetime
from wpnngw.util import inn_config, QueueDir

QROOT=os.path.join(inn_config()['pathspool'],'wpnngw_incoming')

if __name__ == '__main__':
	addresses = sys.argv[1:]
	if addresses and addresses[0].endswith('@wpnngw.local'):
		group = addresses[0].rstrip('@wpnngw.local')
		now = datetime.timestamp(datetime.now())
		qfile = QueueDir(QROOT).newfile("%s-%s" % (group, now))
		with open(qfile, 'w') as qfd: qfd.write(sys.stdin.read())
		qfd.close()

	elif addresses[0] == 'usenet':
		# innd initialization?
		sys.stderr.write("gwmail initialized\n")
	else:
		raise ValueError("%s is not a moderator address" % addresses[0])
		# silently fail to send mail -- oops! >:-)
		sys.exit(0)

