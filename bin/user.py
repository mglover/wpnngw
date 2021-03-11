#!/usr/bin/env python3
#user.py
#manage a flat-file of usernames and passwords

import os, sys, crypt, getpass, random
from wpnngw.util import inn_config

userfile = os.path.join(inn_config()['pathspool'], "users")

def fatal(msg):
	sys.stderr.write(msg+'\n')
	sys.exit(1)

def readusers(file):
	try:
		fp = open(file, 'r')
	except FileNotFoundError: return {}
	return dict([line.split(':') for line in fp.readlines()])

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
	if len(sys.argv) < 3: fatal("user.py command username") 
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
