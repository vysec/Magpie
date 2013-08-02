#!/usr/bin/env python

from main import database

db = database()
print db.pull_unfinished_queue()