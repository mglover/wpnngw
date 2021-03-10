"""
article.py
"""

import email.message, email.policy, textwrap, requests, json, re
from bs4 import BeautifulSoup
from wpnngw.util import debug, utc_datetime, iso_datestr, rfc_datestr, utc_now


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


class MessageID(object):
	def __init__(self):
		self.category = None
		self.uid = None
		self.domain = None

	@classmethod
	def fromString(cls, idstr):
		if not idstr: return None
		self = cls()
		postid, self.domain = re.search("^<([^@]*)@([^>]*)>$", idstr).groups()
		self.category, self.uid = postid.split('-')
		return self

	@classmethod
	def fromArticle(cls, art):
		self = cls()
		self.category = art.wptyp
		self.uid = art.wpid
		# XXX wrong for crossposted articles
		self.domain = art.groups[0]
		return self

	def asString(self):
		return "<%s-%s@%s>" % (self.category, self.uid, self.domain)


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


	def text_from_html(self, raw_content):
		""" convert the raw HTML to something more newsreader-friendly
		"""
		soup = BeautifulSoup(raw_content,features='lxml')
		social_footer = soup.find(class_='sharedaddy')
		if social_footer:
			social_footer.replaceWith('')
		for a in soup('a'):
			if 'href' in a and a.text != a.attrs['href']:
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

		msgid = MessageID.fromString(msg['Message-ID'])
		if msgid:
			self.wptyp = msgid.category
			self.wpid = msgid.uid

		self.groups = msg['Newsgroups'].split(',')
		self.title = msg['Subject']

		if 'Date' in msg:
			self.date_utc = utc_datetime(msg['Date'])
		else:
			self.date_utc = utc_now()

		if 'From' not in msg or not len(msg['From'].addresses):
			raise ValueError("Missing required 'From:' address")
		frm = msg['From'].addresses[0]
		self.author_name = frm.display_name
		self.author_email = frm.username+'@'+frm.domain

		# XXX fails on cross-posted articles
		self.references = MessageID.fromString(msg['References'])

		self.content = unwrap(msg.get_content())

		return self


	def asWordPress(self):
		post = {
			'date_gmt': iso_datestr(self.date_utc),
			'author_name': self.author_name,
			'author_email': self.author_email,
			'content' : self.content,
			'post': int(self.references.uid)
		}
		return post


	@classmethod
	def fromWordPressGeneric(cls, history, art):
		self = cls()
		self.groups.append(history['group'])
		self.date_utc = utc_datetime(art['date_gmt'])
		self.author_name = art.get('author_name')
		self.wpid = art['id']
		self.content = art['content']['rendered']

		updated = utc_datetime(history['updated'])
		if self.date_utc > updated:
			history['updated'] = iso_datestr(self.date_utc)

		return self

	@classmethod
	def fromWordPressPost(cls, history, post):
		debug('adding post id %s' % post['id'])

		self = cls.fromWordPressGeneric(history, post)

		site = history['source']

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

		msg['Date'] = rfc_datestr(self.date_utc)
		if self.author_email: frm_email = self.author_email 
		else: frm_email = "poster@email.invalid"
		msg['From'] = '"%s" <%s>' % (self.author_name, frm_email)
		msg['Message-ID'] = MessageID.fromArticle(self)
		msg['Newsgroups'] = ','.join(self.groups)
		msg['Path'] = 'not-for-mail'
		msg['Subject'] = self.title
		#if article.get('status') == 'approved': XXX only works for comments!
		msg['Approved'] = 'moderator@email.invalid'
		if self.references:
			msg['References'] = [self.references.asString()]

		content = self.text_from_html(self.content)
		msg.set_content(content, cte='quoted-printable')

		return msg.as_string()


	def filename(self):
		if self.wptype == 'post':
			return '00post-%s' % self.wpid
		else:
			return 'comment-%s-%s' % (self.references[0].uid, self.wpid)


