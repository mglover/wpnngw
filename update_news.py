#!/usr/bin/env python3
""" post_to_newsgroup.py
    convert the post at sys.argv[1] 
    and maybe the comments on that post
    to a NetNews pseudo-article(s)
"""

import os, json, sys, subprocess, requests
import email.message, email.policy, textwrap
from datetime import datetime, timezone
from dateutil import parser as dateparser
from bs4 import BeautifulSoup

print_debugging = False

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


def maybe_wrap(para):
	"""wrap paragraphs that are not primarily URLs
	"""
	s=e=para.find('http')
	if e != -1:
		while e<len(para) and not para[e].isspace(): e+=1
		if e-s > len(para)/2: return para
	return '\n'.join(textwrap.wrap(para))


def unwrap(text):
	"""remove all 'wrapping' newlines, but preserve '\n\n' sequences
	"""
	return re.sub('[^\n]\n[^\n]', '', text)


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


class Article(object):
	def __init__(self):
		self.groups = []
		self.author_name = None
		self.author_email = None
		self.date_utc = None
		self.wpid = None
		self.content = None

		self.title = None
		self.wptype = None
		self.subject = None
		self.references = []

		#self.path = None
		#self.approved = None


	def msgid(self, typ=None, wpid=None):
		if not typ: typ = self.wptype
		if not wpid: wpid = self.wpid
		return "<%s-%s@%s>" % (typ, wpid, self.groups[0])

	def parse_msgid(self, msgid):
		postid, group0 = re.search("^<([^@]*)@([^>]*)>$", msgid).groups()
		self.wptype, self.wpid = postid.split('-')

	@classmethod
	def fromNetNews(cls, text):
		""" parse a NetNews article, returning
			a Wordpress-API-ready dictionary
			XXX does not support cross-posted articles
		"""
		parser = email.parser.Parser(policy=email.policy.default)
		msg = parser.parsestr(text)

		self = cls()
		self.parse_msgid(msg['Message-ID'])
		self.groups = msg['Newsgroups']
		self.title = msg['Subject']
		self.wpid = self.parse_msgid()

		if 'Date' in msg:
			date = dateutil.parser.parse(msg['Date'])
			self.date_utc = date + date.utcoffset()
		else:
			self.date_utc = datetime.now(timezone.utc)

		if 'From' not in msg or not len(msg['From'].addresses):
			raise ValueError("Missing required 'From:' address")
		frm = msg['From'].addresses[0]
		self.author_name = frm.display_name
		self.author_email = frm.username+'@'+frm.domain

		self.references = postid_from_references(msg['References'])

		self.content = unwrap(msg.get_content())

		return post, msg['Newsgroups']


	def asWordPress(self):
		post = {
			date_gmt: datetime.strftime(date_utc, "%Y-%m-%dT%H:%M:%SZ"),
			author_name: self.author_name,
			author_email: self.author_email,
			content : self.content
		}
		return post


	@classmethod
	def fromWordPressGeneric(cls, history, art):
		self = cls()
		self.groups.append(history['group'])
		self.date_utc = art['date_gmt']
		self.author_name = art.get('author_name')
		self.wpid = art['id']
		self.content = art['content']['rendered']

		if self.date_utc > history['updated']:
			history['updated'] = self.date_utc

		return self

	@classmethod
	def fromWordPressPost(cls, history, post):
		debug('adding post id %s' % post['id'])

		self = cls.fromWordPressGeneric(history, post)

		self.wptype='post'
		self.title = post['title']['rendered']
		self.author_name = author_from_id(site, post['author'])

		history['posts'][post['id']] = self.title
		return self


	@classmethod
	def fromWordPressComment(cls, history, comment):
		pid = str(comment['post'])
		if pid not in history['posts']:
			debug("skip comment for %s type(%s), not in %s" %
				 (pid, type(pid), history['posts']))
			return None

		self = cls.fromWordPressGeneric(history, comment)

		self.wptype = 'comment'
		self.title = history['posts'][pid]
		self.references = [pid]

		return self


	def asNetNews(self):
		""" convert a (munged) WordPress API article dictionary
			to a NetNews article suitable for posting
		"""

		msg = email.message.EmailMessage()

		msg['Date'] = rfc_date(self.date_utc)
		if self.author_email: frm_email = self.author_email 
		else: frm_email = "poster@email.invalid"
		msg['From'] = '"%s" <%s>' % (self.author_name, frm_email)
		msg['Message-ID'] = self.msgid()
		msg['Newsgroups'] = ','.join(self.groups)
		msg['Path'] = 'not-for-mail'
		msg['Subject'] = self.title
		#if article.get('status') == 'approved': XXX only works for comments!
		msg['Approved'] = 'moderator@email.invalid'
		if self.references:
			msg['References'] = self.msgid('post', self.references[0])

		content = format_content(self.content)
		msg.set_content(content, cte='quoted-printable')

		return msg.as_string()


	def filename(self):
		if self.wptype == 'post':
			return '00post-%s' % self.wpid
		else:
			return 'comment-%s-%s' % (self.references[0], self.wpid)


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

	def unpage(self, url, **params):
		""" Page through WP API responses until we have all the data
		"""
		params['page'] = 1
		if 'per_page' not in params: params['per_page'] = 100
		adicts = []

		while True:
			resp = requests.get(url, params)
			new_dicts = json.loads(resp.text)
			if type(new_dicts) is dict:
				# error response
				fatal(resp.text)
			adicts += new_dicts
			if len(new_dicts) < params['per_page']: return adicts
			params['page'] += 1


	def articles_fetch(self):
		history = self.history_load()
		site = history['source']
		after = iso_datetime(history['updated'])

		new_posts = [Article.fromWordPressPost(history, p)
			for p in self.unpage(site+'/wp-json/wp/v2/posts', after=after)]

		new_comments = [Article.fromWordPressComment(history, c)
			for c in self.unpage(site+'/wp-json/wp/v2/comments', after=after)]

		print('%d new posts, %d new comments' %
			(len(new_posts), len(new_comments)))


		for a in new_posts + new_comments:
			path = os.path.join(self.rundir, a.filename())
			debug(path)
			postfile=open(path, 'w', encoding='utf8', newline=None)
			postfile.write(a.asNetNews())
			postfile.close()

		self.history_save(history)


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
		g.articles_fetch()
		g.articles_post()
