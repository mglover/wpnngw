#!/usr/bin/env python3
"""
post_comment.py
post a comment on a wordpress post
"""

import sys, os, re, email.parser, email.policy, json, requests, dateutil
from datetime import datetime, timezone


def post_comment(site, post_data):
	url = site + '/wp-json/wp/v2/comments'
	json_data = json.dumps(post_data)
	print ('posting to %s with data %s' % (url, json_data))
	resp = requests.post(url, json=json_data)
	open('debug.post', 'w').write(resp.text)
	print('response status %s: headers: %s' % 
		(resp.status_code, resp.headers))

def postid_from_references(ref):
	"""convert a References: value to a wordpress post id
	"""
	s = ref.index('<')
	e = ref.index('@')
	if s == -1 or e == -1 or s>=e:
		raise ValueError("malformed References: %s" % ref)
	local = ref[s+1:e]
	if not local.startswith('post-'):
		raise ValueError("Invalid References: %s" % ref)
	postid = local.lstrip('post-')
	if not postid.isdigit():
		raise ValueError("Post id not a number: %s" % postid)
	return postid


def unwrap(text):
	"""remove all 'wrapping' newlines, but preserve '\n\n' sequences
	"""
	return re.sub('[^\n]\n[^\n]', '', text)


def parse_message(msgtext):
	""" parse a NetNews article, returning a tuple of
		a Wordpress-API-ready dictionary
		and the name of the newsgroup the article was posted to
		XXX does not support cross-posted articles
	"""
	parser = email.parser.Parser(policy=email.policy.default)
	msg = parser.parsestr(msgtext)
	post = {}

	if 'Date' in msg:
		date = dateutil.parser.parse(msg['Date'])
		date_utc = date + date.utcoffset()
	else:
		date_utc = datetime.now(timezone.utc)
	post['date_gmt'] = datetime.strftime(date_utc, "%Y-%m-%dT%H:%M:%SZ")

	if 'From' not in msg or not len(msg['From'].addresses):
		raise ValueError("Missing required 'From:' address")
	frm = msg['From'].addresses[0]
	post['author_name'] = frm.display_name
	post['author_email'] = frm.username+'@'+frm.domain

	post['post'] = postid_from_references(msg['References'])

	post['content'] = unwrap(msg.get_content())

	return post, msg['Newsgroups']


if __name__ == '__main__':
	if sys.argv[1] == '--': fp = sys.stdin
	else: fp = open(sys.argv[1])
	msgtext = fp.read()
	post_data, group = parse_message(msgtext)

	groups = os.listdir('groups')
	hist = json.load(open(os.path.join('groups',  group, 'history.json')))
	site = hist['source']

	post_comment(site, post_data)
