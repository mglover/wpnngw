#!/usr/bin/env python3
""" wp2nn.py
 	fetch comments from gatewayed wordpress sites
	and post them to the correct netnews groups
"""
import sys
from wpnngw.gwgroup import GatewayedGroup

def pull_wordpress(groups):
	for group in groups:
		g = GatewayedGroup(group)
		g.wordpress_fetch()
		g.netnews_post()


if __name__ == '__main__':
	pull_wordpress(sys.argv[1:])
