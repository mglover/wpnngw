#!/usr/bin/env python3
""" wp2nn.py
 	fetch comments from gatewayed wordpress sites
	and post them to the correct netnews groups
"""
import sys, os
from wpnngw.gwgroup import GatewayedGroup

def pull_wordpress(groups):
	for group in groups:
		g = GatewayedGroup(group)
		g.wordpress_fetch()
		g.netnews_post()


if __name__ == '__main__':
	groups = sys.argv[1:]
	if not groups:
		groups = os.listdir(GatewayedGroup.root)
	if len(groups) == 0: print("no groups found")
	pull_wordpress(groups)
