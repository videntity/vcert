#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4


import OpenSSL
import json, sys

def get_revoked_serials(path_to_crl):
    revoked_list = []
    with open(path_to_crl, 'r') as _crl_file:
        crl = "".join(_crl_file.readlines())
    
    crl_object = OpenSSL.crypto.load_crl(OpenSSL.crypto.FILETYPE_PEM, crl)
    
    revoked_objects = crl_object.get_revoked()
    
    for rvk in revoked_objects:
        revoked_list.append(rvk.get_serial())
    return revoked_list

if __name__ == "__main__":
    if len(sys.argv)!=2:
        print "Usage: python get_revoked.py [filepath]"
        sys.exit(1)
    rs = get_revoked_serials(sys.argv[1])
    print json.dumps(rs)