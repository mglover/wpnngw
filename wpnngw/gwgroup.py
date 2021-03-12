"""
gwgroup.py
"""

import json, os, subprocess, requests
from wpnngw.article import Article
from wpnngw.util import fatal, debug, iso_datestr, utc_datetime, \
	inn_config, QueueDir

class GroupStatus(object):
	def __init__(self, grpobj):
		self.load(os.path.join(grpobj.dir(), 'history.json'))

	def load(self, file=None):
		if file: self.file = file
		if not file: raise ValueError("no filename stored or given")
		self.data =  json.load(open(self.file))
		for k in ['source', 'group', 'posts', 'updated']:
			assert k in self.data

	def save(self):
		json.dump(self.data, open(self.file, 'w'), indent=1)
		pass


	def last_update(self):
		return utc_datetime(self.data['updated'])

	def maybe_update(self, newdate):
		olddate = utc_datetime(self.data['updated'])
		if newdate > olddate:
			self.data['updated'] = iso_datestr(newdate)


	def get_site(self):
		return self.data['source']

	def get_group(self):
		return self.data['group']


	def get_post(self,post_id):
		post_id = str(post_id)
		if post_id not in self.data['posts']:
			debug("skip comment for %s type(%s), not in %s" %
				 (post_id, type(post_pid), self.data['posts']))
		return self.data['posts'].get(str(post_id), False)

	def add_post(self, post_id, title):
		self.data['posts'][str(post_id)] = title


class GatewayedGroup(object):
	def __init__(self, group):
		self.group = group
		self.queue = QueueDir(os.path.join(self.dir(), 'queue'))
		self.status = GroupStatus(self)

	def dir(self):
		"""return the path to the directory containing gatewayed group dirs
		"""
		home = inn_config()['pathspool']
		return os.path.join(home, 'wpnngw', 'groups', self.group)

	def exists(self):
		return os.path.isdir(self.dir()) and self.queue.exists()

	def create(self):
		if not self.exists():
			if not os.path.isdir(self.dir()): os.mkdir(self.dir())
		self.queue.create()


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

	def _process_pages(self, category, proc, after):
		site = self.status.get_site()
		url = site + '/wp-json/wp/v2/' + category

		try:
			articles = [proc(self.status, a)
				for a in self.unpage(url, after=after)]
		except requests.exceptions.ConnectionError:
			print('%s: connection to %s failed' % (self.group,site))
			return 0

		for a in articles:
			if not a: continue
			path = self.queue.newfile(a.filename())
			postfile=open(path, 'w', encoding='utf8', newline=None)
			postfile.write(a.asNetNews())
			postfile.close()

		return len(articles)


	def wordpress_fetch(self):
		after = self.status.last_update()
		site = self.status.get_site()

		plen = self._process_pages('posts', Article.fromWordPressPost, after)
		clen = self._process_pages('comments', Article.fromWordPressComment, after)

		print('%s: %d new posts, %d new comments' % (self.group, plen, clen))
		self.status.save()


	def netnews_post(self):
		self.queue.process(lambda x: subprocess.run(['inews', '-h', '-O', x]))
		errors = self.queue.errors()
		if errors:
			fatal("%d articles in %s have errors" 
				% (len(errors), self.queue.cur))


	def wordpress_post(self, post_data):
		site = self.status.get_site()
		url = site + '/wp-json/wp/v2/comments'
		resp = requests.post(url, json=post_data)
		debug("Status: %d\n\nRequest: \n%s\n\nResponse:\n%s" 
			% (resp.status_code, resp.request.body, resp.text))
		return resp.status_code == 201


