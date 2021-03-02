#!/usr/bin/env python3
"""
post_comment.py
post a comment on a wordpress post
"""

import sys, os, json, requests
from wpnngw.article import Article

def post_comment(site, post_data):
	url = site + '/wp-json/wp/v2/comments'
	json_data = json.dumps(post_data)
	print ('posting to %s with data %s' % (url, json_data))
	resp = requests.post(url, json=json_data)
	open('debug.post', 'w').write(resp.text)
	print('response status %s: headers: %s' % 
		(resp.status_code, resp.headers))


if __name__ == '__main__':
	if sys.argv[1] == '--': fp = sys.stdin
	else: fp = open(sys.argv[1])
	msgtext = fp.read()

	art = Article.fromNetNews(msgtext)
	group = art.group[0]
	post_data = Article.asWordPress()

	hist = json.load(open(os.path.join('groups',  group, 'history.json')))
	site = hist['source']

	post_comment(site, post_data)
