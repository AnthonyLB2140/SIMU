#!/usr/bin/python
# coding: utf-8

import os

# Expected command line from the client
print("--appid %d" % int(os.getenv('VTS_APPLICATION_ID', 100)))
