#!/usr/bin/env python3
#user.py
#manage a flat-file of usernames and passwords

import os, sys, crypt, getpass, random
from wpnngw.util import inn_config, fatal

userfile = os.path.join(inn_config()['pathdb'], "users")

def readusers(file):
	line = ''
	try:
		fp = open(file, 'r')
		return dict([line.split(':')
					for line in fp.readlines()
					if len(line)])
	except FileNotFoundError:
		return {}

def writeusers(file, users):
	fp = open(file, 'w')
	fp.write('\n'.join([':'.join([u,p]) for u,p in users.items()])+'\n')
	fp.close()

def getsalt():
	a = random.choice(list('abcdefghijklmnopqrstuvwxyz'))
	b = random.choice(list('abcdefghijklmnopqrstuvwxyz'))
	return a+b

def adduser(user, passwd):
	users = readusers(userfile)
	if user in users: fatal("user exists: %s" % user)
	users[user] = crypt.crypt(passwd, getsalt())
	writeusers(userfile, users)

def passwd(user, passwd):
	users = readusers(userfile)
	if user not in users: fatal("no such user: %s" % user)
	users[user] = crypt.crypt(passwd, getsalt())
	writeusers(userfile, users)

def deluser(user):
	users = readusers(userfile)
	if user not in users: fatal("no such user: %s" % user)
	del users[user]
	writeusers(file, users)


if __name__ == '__main__':
	if len(sys.argv) < 3: fatal("user.py [ add | del | passwd ] <username>")
	cmd = sys.argv[1]
	user = sys.argv[2]
	if 'add' == cmd:
		adduser(user, getpass.getpass())
	elif 'passwd' == cmd:
		passwd(user, getpass.getpass())
	elif 'del' == cmd:
		deluser(user)
	else: 
		fatal("unrecognized command: %s" % cmd)
