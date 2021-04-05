#! /usr/bin/env python3
""" fill_gaps.py
    find gaps in (strictly increasing) comment ids from WordPress
    examine the gap-adjacent articles to find the associated date range
 	and re-query WP for potentially missing comments.
"""

import os, sys, math
from datetime import datetime, timedelta
from wpnngw.util import QueueDir, inn_config, iso_datestr, utc_now
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.article import Article


def is_article_after(dir, file, after_date):
	art = Article.fromNetNewsFile(os.path.join(dir, file))
	return art.date_utc > after_date


def cid_from_filename(filename):
	return int(filename.split('-')[2])


def cids_after(dir, after_date):
	""" return a list of (id, path) tuples
		of comments posted after after_date
	"""
	all_files = list(filter(lambda x: not x.startswith('0'), os.listdir(dir)))
	all_files.sort(key=cid_from_filename)

	idx = len(all_files)-1
	step = math.floor(math.sqrt(idx))
	done = False
	while not done:
		if idx < 0:
			idx=0
			done=True
		else:
			done = not is_article_after(dir, all_files[idx], after_date)
		if not done:
			idx -= step

	done=False
	while not done:
		last_idx = idx
		idx +=1
		done = is_article_after(dir, all_files[idx], after_date)

	return [(cid_from_filename(f), os.path.join(dir, f))
		for f in all_files[idx:] if 'comment' in f]


def fill_gaps(groupname, **kwargs):
	group = GatewayedGroup(groupname)

	dir = group.queue.fin
	after_date = utc_now() - timedelta(**kwargs)

	print("%s: searching gaps after %s" 
		% (groupname, datetime.strftime(after_date, '%c')))

	cids = cids_after(dir, after_date)

	if len(cids) == 0: 
		print ("no comments since %s" % after_date)
		return

	gaps = []
	last_cid, last_file = cids.pop(0)
	for (cid, file) in cids:
		if cid > int(last_cid) + 1:
			art = Article.fromNetNewsFile(os.path.join(dir, file))
			last_art = Article.fromNetNewsFile(os.path.join(dir, last_file))
			print("%d:%s -> %d:%s" % (last_cid, last_art.date_utc,
				cid, art.date_utc))
			gaps.append((last_art.date_utc, art.date_utc))
		last_cid = cid
		last_file = file

	print("%d gaps" % len(gaps))

	for g in gaps:
		start, end = g
		group.wordpress_fetch(after=start, before=end, posts=False)
		group.netnews_post()


if __name__ == '__main__':
	groups = sys.argv[1:]
	if not groups:
		groups = os.listdir(GatewayedGroup.root)
	if len(groups) == 0: print("no groups found")
	for g in groups:
		fill_gaps(g, weeks=2)

