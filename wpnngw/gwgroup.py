"""
gwgroup.py
"""

import json, os, subprocess, requests
from wpnngw.article import Article
from wpnngw.util import fatal, debug, utc_datetime, groupsdir, QueueDir


class GatewayedGroup(object):
	def __init__(self, group):
		self.group = group
		dir = groupsdir()
		self.groupdir = os.path.join(dir, group)
		self.histfile = os.path.join(self.groupdir, 'history.json')


	def exists(self):
		return os.path.isdir(self.groupdir)

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


	def wordpress_fetch(self):
		history = self.history_load()
		site = history['source']
		after = utc_datetime(history['updated'])

		try:
			new_posts = [Article.fromWordPressPost(history, p)
				for p in self.unpage(site+'/wp-json/wp/v2/posts', after=after)]

			new_comments = [Article.fromWordPressComment(history, c)
				for c in self.unpage(site+'/wp-json/wp/v2/comments', after=after)]
		except requests.exceptions.ConnectionError:
			print('%s: connection to %s failed' % (self.group,site))
			return
		else:
			print('%s: %d new posts, %d new comments' %
				(self.group, len(new_posts), len(new_comments)))


		for a in new_posts + new_comments:
			if not a: continue
			path = QueueDir(self.groupdir).newfile(a.filename())
			postfile=open(path, 'w', encoding='utf8', newline=None)
			postfile.write(a.asNetNews())
			postfile.close()

		self.history_save(history)


	def netnews_post(self):
		active = os.path.join(self.groupdir, 'active')
		processed = os.path.join(self.groupdir, 'processed')

		qdir = QueueDir(self.groupdir)
		qdir.process(lambda x: subprocess.run(['inews', '-h', '-O', x]))
		errors = qdir.errors()
		if errors:
			fatal("%d articles in %s have errors" % (len(errors), qdir.cur))


	def wordpress_post(self, post_data):
		history = self.history_load()
		site = history['source']

		url = site + '/wp-json/wp/v2/comments'
		resp = requests.post(url, json=post_data)
		print("Status: %d\n\nRequest: \n%s\n\nResponse:\n%s" 
			% (resp.status_code, resp.request.body, resp.text))
		return resp.status_code == 201


