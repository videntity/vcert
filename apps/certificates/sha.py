#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


import os, sys, hashlib

def sha1_from_filepath(fp):
    f = open(fp, 'r')
    m = hashlib.sha1()
    m.update(f.read())
    f.close()
    return m.hexdigest()

def sha256_from_filepath(fp):
    f = open(fp, 'r')
    m = hashlib.sha256()
    m.update(f.read())
    f.close()
    return m.hexdigest()


  
if __name__ == "__main__":
    if len(sys.argv)!=2:
        print "Usage: python sha.py [filepath]"
        sys.exit(1)
    print sha256_from_filepath(sys.argv[1])
        
    
    