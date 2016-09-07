# Perform file hashes
# http://stackoverflow.com/a/3431835

# coding: utf-8

import hashlib

def hash_string(s, hasher):
	hasher.update(s)
	return hasher.hexdigest()

def hash_file(filename, hasher, blocksize=65536):
	with open(filename, 'rb') as f:
		buf = f.read(blocksize)
		while len(buf) > 0:
			hasher.update(buf)
			buf = f.read(blocksize)
		return hasher.hexdigest()

def md5_file(filename):
	return hash_file(filename, hashlib.md5())

def md5(s):
	return hash_string(hashlib.md5())

def sha256_file(filename):
	return hash_file(filename, hashlib.sha256())

def sha256(s):
	return hash_string(s, hashlib.sha256())
