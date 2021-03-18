#!/usr/bin/env python3
""" gwmail.py
	intercept mail for WordPress-gatewayed groups
	and post those articles through the blog's approval system
"""

import os, sys, subprocess
from datetime import datetime

sys.path.append('/usr/local/news/spool/wpnngw')

from wpnngw.util import inn_config, QueueDir

QROOT=os.path.join(inn_config()['pathspool'],'wpnngw', 'modqueue')

if __name__ == '__main__':
	addresses = sys.argv[1:]
	qdir = QueueDir(QROOT)
	qdir.create()

	if addresses and addresses[0].endswith('@wpnngw.local'):
		group = addresses[0].rstrip('@wpnngw.local')
		now = datetime.timestamp(datetime.now())
		qfile = qdir.newfile("%s-%s" % (group, now))
		with open(qfile, 'w') as qfd: qfd.write(sys.stdin.read())
		qfd.close()

	else:
		ret = subprocess.run(["/usr/sbin/sendmail", "-oi", "-oem", sys.argv[1])
		sys.exit(ret.returncode)

