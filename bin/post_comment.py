#!/usr/bin/env python3
"""
post_comment.py
post a comment on a wordpress post
"""

import sys, os, json, requests
from datetime import datetime
from wpnngw.article import Article
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.util import debug, fatal


lf = open('/var/spool/news/wpnngw/post_comment.log', 'w')
def log(msg):
	lf.write("%s: %s\n" %  (datetime.isoformat(datetime.now()), msg))
	lf.flush()
	os.fsync(lf)

if __name__ == '__main__':
	if sys.argv[1] == '--': fp = sys.stdin
	else: fp = open(sys.argv[1])
	msgtext = fp.read()

	log("read message")
	try:
		art = Article.fromNetNews(msgtext)
		post_data = art.asWordPress()
	except Exception as e:
		log("caught in parsing: %s" % str(e))
		log("article written to /var/spool/news/wpnngw/dead_article.log")
		mf = open("/var/spool/news/wpnngw/dead_article.log", 'w')
		mf.write(msgtext)
		mf.flush()
		os.fsync(mf)
		sys.exit(11)
	log("post data parsed")
	for g in art.groups:
		resp = GatewayedGroup(g).wordpress_post(post_data)
		if resp.status_code != 201:
			log('posting failed with code %d' % resp.status_code)
			fatal("Posting to %s failed: \n\nRequest:\n%s\n\nResponse:\n%s" % 
				(g, resp.request.body, resp.text))
	log ("Posted to %d groups" % len(art.groups))
	sys.exit(0)
