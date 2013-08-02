#!/usr/bin/env python

from flask import Flask, render_template, Markup, request, session, redirect, url_for
import sqlite3 as lite
import time
import bcrypt

Settings = {
	'DBFile': 'storage.db',
	'Debug': True,
	'DefaultPassword': 'password', # Do change this before starting the script.
	'NetworkHost': '0.0.0.0',
	'NetworkPort': 3000,
	'ServiceName': 'Hash Cracker',
	'SubmitDelay': 5, # Delay between hash submissions in minutes for users.
}
Strings = {
	'HashInvalid': 'Submitted hash is invalid.',
	'HashStates': { 0: 'Queued', 1: 'In progress', 2: 'Complete' },
}

class database:
	def __init__(self):
		try:
			open(Settings['DBFile']).close()
			create = False
		except:
			create = True
		self.db = lite.connect(Settings['DBFile'])
		if create:
			q = 'CREATE TABLE "queue" ("ID" INTEGER PRIMARY KEY  NOT NULL ,"UserID" INTEGER DEFAULT (0) ,"TimeSecs" INTEGER,"HashString" VARCHAR,"Type" VARCHAR,"IPAddress" VARCHAR,"Status" INTEGER DEFAULT (0) , "Result" VARCHAR DEFAULT 0)'
			self.cur.execute(q)
			q = 'CREATE TABLE "main"."users" ("ID" INTEGER PRIMARY KEY  AUTOINCREMENT  NOT NULL  UNIQUE , "Username" VARCHAR, "Password" VARCHAR, "TimeStamp" INTEGER, "PasswordSalt" VARCHAR, "LastIP" VARCHAR)'
			self.cur.execute(q)

	def add_queue(self, hashstr, ipaddress):
		with self.db as con:
			cur = con.cursor()
			q = 'INSERT INTO queue (UserID, TimeSecs, HashString, Type, IPAddress) VALUES (?, ?, ?, ?, ?)'
			cur.execute(q, (0, time.time(), hashstr, 0, ipaddress))

	def pull_unfinished_queue(self):
		with self.db as con:
			con.row_factory = lite.Row
			cur = con.cursor()
			q = 'SELECT * FROM queue ORDER BY TimeSecs DESC LIMIT 10'
			cur.execute(q)
			data = cur.fetchall()
			if len(data) == 0:
				return ''
			else:
				output = []
				count = 0
				for row in data:
					print row
					count = count + 1
					item = {}
					item['JobID'] = row[0]
					item['Count'] = count
					item['Hash'] = row[3]
					item['Time'] = row[2]
					item['User'] = row[1]
					item['Status'] = row[5]
					item['StatusHuman'] = Strings['HashStates'][row[6]]
					output.append(item)
				return output

app = Flask(__name__)

@app.route('/')
def Main(defaults = None):
	int_db = database()
	CurrentHashes = int_db.pull_unfinished_queue()
	if defaults == None:
		CurrentSettings = DefaultSettings()
	else:
		CurrentSettings = defaults
	return render_template('main.html', 
		ValueErrorMessage = CurrentSettings['ValueError']['Message'],
		ValueQueueHashes = CurrentHashes,
		ValuePageTitle = CurrentSettings['ValueTitle'],

		RenderError = CurrentSettings['ValueError']['State'],
		)

@app.route('/submit', methods=[ 'POST' ])
def Submit():
	CurrentSettings = DefaultSettings()
	# Check to make sure it is a valid hash (MD5, SHA, etc)
	if len(request.form['hash']) in [ 32, 40, 64 ]:
		valid_char = [ str(x) for x in range(0, 10) ] + [ chr(x) for x in range(97, 103) ]
		invalid_hash = False
		for char in request.form['hash'].lower():
			if char not in valid_char:
				invalid_hash = True
		if invalid_hash:
			CurrentSettings['ValueError']['State'] = True
			CurrentSettings['ValueError']['Message'] = Strings['HashInvalid']
		else:
			int_db = database()
			int_db.add_queue(hashstr=request.form['hash'], ipaddress=request.remote_addr)
	else:
		CurrentSettings['ValueError']['State'] = True
		CurrentSettings['ValueError']['Message'] = Strings['HashInvalid']
	return Main(CurrentSettings)

'''
None-render functions
'''

def DefaultSettings():
	return {
		'ValueError': { 'State': False, 'Message': '' },
		'ValueTitle': Settings['ServiceName'],
	}

def DateString(value, format='%H:%M / %d-%m-%Y'):
    return time.strftime(format, value)

if __name__ == '__main__':
	app.run(debug=Settings['Debug'], port=Settings['NetworkPort'], host=Settings['NetworkHost'])
	CGIHandler().run(app)
	db = database()