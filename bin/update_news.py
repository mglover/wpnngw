#!/usr/bin/env python3
""" post_to_newsgroup.py
    convert the post at sys.argv[1] 
    and maybe the comments on that post
    to a NetNews pseudo-article(s)
"""

import sys
from wpnngw.gwgroup import GatewayedGroup

if __name__ == '__main__':
	for group in sys.argv[1:]:
		g = GatewayedGroup('groups', group)
		g.articles_fetch()
		g.articles_post()
