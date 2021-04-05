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
				 (post_id, type(post_id), self.data['posts']))
		return self.data['posts'].get(str(post_id), False)

	def add_post(self, post_id, title):
		self.data['posts'][str(post_id)] = title


	def get_gap_cid(self):
		return int(self.data.get('gap_cid', 0))

	def set_gap_cid(self,cid):
		self.data['gap_cid'] = cid


class GatewayedGroup(object):
	root = os.path.join(inn_config()['pathspool'], 'wpnngw', 'groups')
	def __init__(self, group):
		self.group = group
		self.queue = QueueDir(os.path.join(self.dir(), 'queue'))
		self.status = GroupStatus(self)

	def dir(self):
		"""return the path to the directory containing gatewayed group dirs
		"""
		return os.path.join(self.root, self.group)

	def exists(self):
		return os.path.isdir(self.dir()) and self.queue.exists()

	def create(self):
		group_root = os.dirname(self.dir())
		if not os.path.isdir(group_root): os.mkdir(group_root)
		if not os.path.isdir(self.dir()): os.mkdir(self.dir())
		self.queue.create()


	def _process_pages(self, category, proc, before=None, after=None):
		site = self.status.get_site()
		url = site + '/wp-json/wp/v2/' + category
		params = {'page': 1, 'after': after, 'per_page': 100}
		if before: params['before'] = before
		if after: params['after'] = after
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

	def wordpress_fetch(self, before=None, after=None, comments=True, posts=True):
		if not after:
			after = self.status.last_update()
		site = self.status.get_site()

		if posts:
			plen = self._process_pages('posts', Article.fromWordPressPost,
				before=before, after=after)
		else: plen = 0

		if comments:
			clen = self._process_pages('comments', Article.fromWordPressComment,
				before=before, after=after)
		else: comments = 0

		print('%s: %d new posts, %d new comments' % (self.group, plen, clen))
		self.status.save()


	def netnews_post(self):
		def proc(x):
			inews = os.path.join(inn_config()['pathbin'], 'inews')
			ret = subprocess.run([inews, '-h', '-O', x])
			return ret.returncode == 0

		self.queue.process(proc)
		errors = self.queue.errors()
		if errors:
			print("%d articles in %s have errors"
				% (len(errors), self.queue.cur))


	def wordpress_post(self, post_data):
		site = self.status.get_site()
		url = site + '/wp-json/wp/v2/comments'
		resp = requests.post(url, json=post_data)
		debug("Status: %d\n\nRequest: \n%s\n\nResponse:\n%s"
			% (resp.status_code, resp.request.body, resp.text))
		return resp.status_code == 201


