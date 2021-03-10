#!/usr/bin/env python3
""" gwmail.py
	intercept mail for WordPress-gatewayed groups
	and post those articles through the blog's approval system
"""

import sys, subprocess
from datetime import datetime

lf = open('/var/spool/news/wpnngw/gwmail.log', 'w')
def log(msg):
	lf.write("%s: %s\n" %  (datetime.isoformat(datetime.now()), msg))
	lf.flush()


if __name__ == '__main__':
	addresses = sys.argv[1:]
	log("received for %s" % addresses)
	if addresses and addresses[0].endswith('@wpnngw.local'):
		log("post_comment")
		ret = subprocess.run(['/var/spool/news/wpnngw/bin/post_comment.py', '--'])
		log("post_comment returned %d" % ret.returncode)
		sys.exit(ret.returncode)
	elif addresses[0] == 'usenet':
		# innd initialization?
		sys.stderr.write("gwmail initialized\n")
	else:
		raise ValueError("%s is not a moderator address" % addresses[0])
		# silently fail to send mail -- oops! >:-)
		sys.exit(0)

