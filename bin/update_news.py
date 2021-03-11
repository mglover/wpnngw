#!/usr/bin/env python3
""" update news.py
	pull new posts and comments from upstream wordpress
	and push netnews up
"""

import sys, os
from requests.exceptions import ConnectionError

from wpnngw.article import Article
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.util import inn_config, QueueDir


QROOT=os.path.join(inn_config()['pathspool'],'wpnngw_incoming')


def post_comment(afile):
	print("posting %s" % afile)
	try:
		msgtext = open(afile).read()
		art = Article.fromNetNews(msgtext)
		post_data = art.asWordPress()
		for g in art.groups:
			grp = GatewayedGroup(g)
			if not grp.exists: continue
			if not grp.wordpress_post(post_data):
				return False
	except Exception as e:
		print("%s raised: %s %s" % (afile, type(e), str(e)))
		return False 
	print("%s ok" % afile)
	return True


def push_netnews():
	qdir = QueueDir(QROOT)
	print('%d articles for netnews' % len(qdir.pending()))
	qdir.process(post_comment)
	errors = qdir.errors()
	if errors: print('%d articles had errors' % len(errors))

def pull_wordpress(groups):
	for group in groups:
		g = GatewayedGroup(group)
		g.wordpress_fetch()
		g.netnews_post()


if __name__ == '__main__':
	pull_wordpress(sys.argv[1:])
	push_netnews()
