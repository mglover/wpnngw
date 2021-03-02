#!/usr/bin/env python3
""" gwmail.py
	intercept mail for WordPress-gatewayed groups
	and post those articles through the blog's approval system
"""

import sys, inn_config

mailer = inn_config.as_dict()['mail"/usr/lib/news/bin/innmail"

def fatal(*args):
	print(*args)
	sys.exit(1)

if __name__ == __main__:
	args = sys.args[1:]
	addresses = []
	subject = None
	mailer = None
	while args:
		arg = args.pop(0)
		elif '-h' == arg:
			print("rtfsc!")
		elif '-s' == arg:
			subject = args.pop(0)
		else
			addresses.append(arg)
	if not addresses:
			fatal("no addresses given")

	if address[0].endswith('@wordpress-gateway.local'):
		ret = subprocess.run(['post_comment.py', '--'])
	else:
		outargs = [mailer]
		if subject:
			outargs += ['-s', subject]
		outargs += addresses
		ret = subprocess.run(outargs)

	sys.exit(ret)
