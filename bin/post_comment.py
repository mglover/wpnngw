#!/usr/bin/env python3
"""
post_comment.py
post a comment on a wordpress post
"""

import sys, os, json, requests
from wpnngw.article import Article
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.util import groupsdir


if __name__ == '__main__':
	if sys.argv[1] == '--': fp = sys.stdin
	else: fp = open(sys.argv[1])
	msgtext = fp.read()

	art = Article.fromNetNews(msgtext)
	post_data = Article.asWordPress()

	for g in groups:
	hist = json.load(open(os.path.join(groupsdir(),  g, 'history.json')))
	site = hist['source']

	g.wordpress_post(site, post_data)
