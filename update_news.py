#!/usr/bin/env python3
""" post_to_newsgroup.py
    convert the post at sys.argv[1] 
    and maybe the comments on that post
    to a NetNews pseudo-article(s)
"""

import os, json, sys, subprocess, requests
import email.message, email.policy, textwrap
from datetime import datetime
from dateutil import parser as dateparser
from bs4 import BeautifulSoup

print_debugging = True

def fatal(msg):
	sys.stderr.write(msg+'\n')
	sys.exit(1)

def debug(*args):
	if print_debugging: print(*args)

def rfc_date(datestr):
	date = dateparser.parse(datestr)
	return datetime.strftime(date, "%d %b %Y %H:%M:%S %z")

def iso_datetime(datestr):
	""" Wordpress API requires a two-digit timezone specifier ???"""
	date = dateparser.parse(datestr)
	return datetime.strftime(date, '%Y-%m-%dT%H:%M:%S-00')

known_authors = {}
def author_from_id(site, id):
	if id not in known_authors:
		resp=requests.get(site+'/wp-json/wp/v2/users/'+str(id))
		known_authors[id] = json.loads(resp.text)['name']
	return known_authors[id]

def msgid_from_group_id(group, id):
	return "<%s@%s>" % (id, group)


def maybe_wrap(para):
	"""wrap paragraphs that are not primarily URLs
	"""
	s=e=para.find('http')
	if e != -1:
		while e<len(para) and not para[e].isspace(): e+=1
		if e-s > len(para)/2: return para
	return '\n'.join(textwrap.wrap(para))


def format_content(raw_content):
	""" convert the raw HTML to something more newsreader-friendly
	    currently: 	remove social media footer,
	    replace IMG with alt text (if non-empty),
	    replace <b>/</b> with *, <ul>/</ul> with _ 
	    insert link url (if different) in parens after link text,
	    then strip all tags and concatenate text,
	    inserting blank lines at paragraph breaks
	    and wrapping at 70 chars.
	"""
	soup = BeautifulSoup(raw_content,features='lxml')
	social_footer = soup.find(class_='sharedaddy')
	if social_footer:
		social_footer.replaceWith('')
	for a in soup('a'):
		if a.text != a.attrs['href']:
			a.replaceWith("%s (%s)" % (a.text, a.attrs['href']))
	for b in soup('b'):
		b.replaceWith('*%s*'%b.text)
	for ul in soup('ul'):
		ul.replaceWith('_%s_'%ul.text)
	for img in soup('img'):
		img.replaceWith("Image: %s(%s)\n" 
			% (img.attrs.get('alt', ''), img.attrs.get('src')))
	return '\n\n'.join([maybe_wrap(para)
		for para in soup.get_text().split('\n')
		if len(para.strip())]
	)


def format_article_json(article):
	""" convert a (munged) WordPress API article dictionary
		to a NetNews article suitable for posting
	"""
#	pol=email.policy.SMTP

	msg = email.message.EmailMessage()

	msg['Date'] = rfc_date(article['date'])
	msg['From'] = '"'+article['author_name']+'"<poster@email.invalid>'
	msg['Message-ID'] = msgid_from_group_id(
		article['newsgroups'], article['id'])
	msg['Newsgroups'] = article['newsgroups']
	msg['Path'] = 'not-for-mail'
	msg['Subject'] = article['title']
	#if article.get('status') == 'approved': XXX only works for comments!
	msg['Approved'] = 'moderator@email.invalid'
	if 'references' in article:
		msg['References'] = article['references']

	content = format_content(article['content']['rendered'])
	msg.set_content(content, cte='quoted-printable')

	return msg.as_string()#.replace('\r\n', '\n')


class GatewayedGroup(object):
	def __init__(self, dir, group):
		self.group = group
		self.groupdir = os.path.join(dir, group)
		self.histfile = os.path.join(self.groupdir, 'history.json')
		self.rundir = os.path.join(self.groupdir, 'incoming')


	def history_load(self):
		return json.load(open(self.histfile))


	def history_save(self, history):
		json.dump(history, open(self.histfile, 'w'), indent=1)


	def articles_fetch(self):
		history = self.history_load()
		site = history['source']
		after = iso_datetime(history['updated'])
		params = {'after': after, 'per_page': 100}

		articles = []
		done = False
		for category in ['posts', 'comments']:
			params['page'] = 1
			done=False
			while not done:
				req = site+'/wp-json/wp/v2/'+category
				#debug(req, params)
				resp = requests.get(req, params)
				new_articles = json.loads(resp.text)
				if type(new_articles) is dict:
					# error response
					fatal(resp.text)
				#open('debug.response', 'w').write(resp.text)
				articles += new_articles
				if len(new_articles) < 100: done=True
				params['page'] += 1

		print('%d new articles' % len(articles))
		return articles


	def articles_munge(self, articles):
		history = self.history_load()
		site = history['source']

		for a in articles:
			if a['date_gmt'] > history['updated']:
				history['updated'] = a['date_gmt']

			a['newsgroups'] = self.group
			if 'title' in a:
				# top-level post
				label='00post'
				debug('adding post id %s' % a['id'])
				history['posts'][a['id']] = a['title']['rendered']
				a['author_name'] = author_from_id(site, a['author'])
				a['title'] = a['title']['rendered']
			else:
				# comment
				pid = str(a['post'])
				if pid not in history['posts']:
					debug("skip comment for %s type(%s), not in %s" %
						 (pid, type(pid), history['posts']))
					continue
				label = 'comment-%s' % pid
				a['title'] = history['posts'][pid]
				a['references'] = msgid_from_group_id(self.group, pid)
			a['id'] = '%s-%s' % (label, a['id'])

		self.history_save(history)
		return articles


	def articles_store(self, articles):
		for a in articles:
			path = os.path.join(self.rundir, a['id'])
			text = format_article_json(a)
			debug(path)
			postfile=open(path, 'w', encoding='utf8', newline=None)
			postfile.write(text)
			postfile.close()


	def articles_post(self):
		incoming = os.path.join(self.groupdir, 'incoming')
		active = os.path.join(self.groupdir, 'active')
		processed = os.path.join(self.groupdir, 'processed')

		for article in os.listdir(incoming):
			i = os.path.join(incoming, article)
			a = os.path.join(active, article)
			p = os.path.join(processed, article)
			os.rename(i, a)
			ret = subprocess.run(['inews', '-h', '-O', a])
			if ret.returncode == 0:
				os.rename(a, p)

		errors = os.listdir(active)
		if errors:
			fatal("%d articles in %s have errors" % (len(errors), active))


if __name__ == '__main__':
	for group in sys.argv[1:]:
		g = GatewayedGroup('groups', group)
		articles = g.articles_munge(g.articles_fetch())
		g.articles_store(articles)
		g.articles_post()
