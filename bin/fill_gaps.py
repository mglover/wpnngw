#! /usr/bin/env python3
""" fill_gaps.py
    find gaps in (strictly increasing) comment ids from WordPress
    examine the gap-adjacent articles to find the associated date range
 	and re-query WP for potentially missing comments.
"""

import os, sys
from wpnngw.util import QueueDir, inn_config, iso_datestr
from wpnngw.gwgroup import GatewayedGroup
from wpnngw.article import Article


def fill_gaps(groupname):
	group = GatewayedGroup(groupname)

	dir = group.queue.fin
	after_cid = group.status.get_gap_cid()

	print("%s: searching gaps after comment %d" % (groupname, after_cid))
	cids = list(filter(lambda x:x[0]>after_cid,
			[(int(f.split('-')[2]), f)
				for f in os.listdir(dir)
				if f.startswith('comment')]))
	cids.sort()

	if len(cids) == 0: 
		print ("no gaps")
		return

	gaps = []
	last_cid, last_file = cids.pop(0)
	for (cid, file) in cids:
		if cid > int(last_cid) + 1:
			art = Article.fromNetNewsFile(os.path.join(dir, file))
			last_art = Article.fromNetNewsFile(os.path.join(dir, last_file))
			gaps.append((last_art.date_utc, art.date_utc))
		last_cid = cid
		last_file = file

	group.status.set_gap_cid(last_cid)
	group.status.save()

	print("%d gaps" % len(gaps))

	for g in gaps:
		start, end = g
		print('filling from %s to %s' % (start, end))
		group.wordpress_fetch(after=start, before=end)
		group.netnews_post()


if __name__ == '__main__':
	groups = sys.argv[1:]
	if not groups:
		groups = os.listdir(GatewayedGroup.root)
	if len(groups) == 0: print("no groups found")
	for g in groups:
		fill_gaps(g)
