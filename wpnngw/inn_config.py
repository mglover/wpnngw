#!/usr/bin/env python3
""" inn_config.py
python interface for reading inn.conf
with no validation for correctness
"""

INNCONF="/etc/news/inn.conf"

def unquote(value):
	"""remove surrounding quotes and remove backslash-quoting
	"""
	assert value.startswith('"') and value.endswith('"')
	value.strip('"')
	value.replace('\\\\', '\\').replace('\\"', '"')
	return value

def as_dict(cfg=INNCONF):
	d = {}
	lineno=1
	for line in open(cfg).readlines():
		if line.startswith('#') or len(line.strip()) == 0: continue
		name, value = line.split(':', 1)
		if name in d: continue
		value = value.strip()
		if value.startswith('"'):
			value = unquote(value)
		d[name] = value
		lineno+=1
	return d
