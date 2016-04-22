#!/usr/bin/python
import argparse
from pymongo import MongoClient

def initDB(url, user, password):
	if len(url.split(':')) == 1:
		dbUrl = 'mongodb://{0}:27017'.format(url)
	else:
		dbUrl = 'mongodb://{0}'.format(url)

	dbClient = MongoClient(dbUrl)
	if user != None and password != None:
		try:
			dbClient.ornaments.authenticate(user, password, source='admin')
		except:
			print "Error, connection to the database is impossible. Most probably the url, user or password is wrong."
			sys.exit()

	return dbClient


parser = argparse.ArgumentParser(description='Copy a collection from a mongodb instance to another one.')
parser.add_argument('dbUrlFrom', type=str, help='Source databse url (to be copied)')
parser.add_argument('-uf', '--userFrom', action="store", dest='dbUserFrom', type=str, nargs='?', help='Source database user')
parser.add_argument('-pf', '--passwordFrom', action="store", dest='dbPasswordFrom', type=str, nargs='?', help='Source database password')
parser.add_argument('dbUrlTo', type=str, help='Destination database')
parser.add_argument('-ut', '--userTo', action="store", dest='dbUserTo', type=str, nargs='?', help='Destination database user')
parser.add_argument('-pt', '--passwordTo', action="store", dest='dbPasswordTo', type=str, nargs='?', help='Destination database password')
args = parser.parse_args()

dbClientFrom = initDB(args.dbUrlFrom, args.dbUserFrom, args.dbPasswordFrom)
dbClientTo = initDB(args.dbUrlTo, args.dbUserTo, args.dbPasswordTo)

oldColl = dbClientFrom.ornaments.books.find()
newColl = dbClientTo.ornaments.books
oldCollSize = oldColl.count()
count = 1
for element in oldColl:
	newColl.insert_one(element)
	print "{0}/{1}".format(count, oldCollSize)
	count += 1

dbClientFrom.close()
dbClientTo.close()