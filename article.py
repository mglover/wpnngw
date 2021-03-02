"""
article.py
"""

import email.message, email.policy
from datetime import datetime, timezone
from bs4 import BeautifulSoup


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


	def text_from_html(raw_content):
		""" convert the raw HTML to something more newsreader-friendly
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

		content = self.text_from_html(self.content)
		msg.set_content(content, cte='quoted-printable')

		return msg.as_string()


	def filename(self):
		if self.wptype == 'post':
			return '00post-%s' % self.wpid
		else:
			return 'comment-%s-%s' % (self.references[0], self.wpid)


