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


	def _process_pages(self, category, proc, after):
		site = self.status.get_site()
		url = site + '/wp-json/wp/v2/' + category
		params = {'page': 1, 'after': after, 'per_page': 100}
		count = 0
		more = True
		try:
			while more:
				resp = requests.get(url, params)
				adicts = json.loads(resp.text)
				if type(adicts) is dict:
					# error response
					raise ValueError(resp.text)

				articles = [proc(self.status, a) for a in adicts]
				for a in adicts:
					art = proc(self.status, a)
					if not art: continue
					art.enqueue(self.queue)
					count += 1

				if len(articles) < params['per_page']: return count
				else: params['page'] += 1

		except (ValueError, requests.exceptions.ConnectionError):
			print('%s: connection to %s failed' % (self.group,site))
			return count

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


