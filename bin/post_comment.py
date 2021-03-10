#!/usr/bin/env python3
"""
post_comment.py
post a comment on a wordpress post
"""

import sys, os, json, requests
from wpnngw.article import Article
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.util import debug, fatal


if __name__ == '__main__':
	if sys.argv[1] == '--': fp = sys.stdin
	else: fp = open(sys.argv[1])
	msgtext = fp.read()

	art = Article.fromNetNews(msgtext)
	post_data = art.asWordPress()

	for g in art.groups:
		resp = GatewayedGroup(g).wordpress_post(post_data)
		if resp.status_code != 200:
			fatal("Posting to %s failed: \n\nRequest:\n%s\n\nResponse:\n%s" % 
				(g, resp.request.body, resp.text))
	print("Posted to %d groups" % len(g))
