#!/usr/bin/python
import sys
import os
import argparse
from pymongo import MongoClient
from library import Library
from book import Book

#Argument parsing
parser = argparse.ArgumentParser(description='Process zipped book from BCUL scanned by Google.')
parser.add_argument('sourceFolder', type=str, help='Source folder of zipped books')
parser.add_argument('-v', '--verbosity', help='Increase output verbosity', action='store_true')
parser.add_argument('-q', '--quiet', help='Reduce output verbosity', action='store_true')
parser.add_argument('-s', '--stats', help='Print statistics at the end', action='store_true')
parser.add_argument('-db', '--populateDB', help='Populate the database with parsed data', action='store_true')
parser.add_argument('-dst', '--destination', action="store", dest='destinationFolder', type=str, nargs='?', help='Destination folder for unzipped images')
parser.add_argument('-n', '--maxBook', action="store", dest='maxParseBook', type=int, nargs='?', help='Maximum number of books to be parse')
args = parser.parse_args()

#Check that the given source folder is a folder
srcDir = args.sourceFolder
if not srcDir.endswith("/"):
	srcDir += "/"
if not os.path.isdir(srcDir):
	print "Error. The path to source directory isn't a directory."
	sys.exit()

#Check that the given destination folder is a folder if any given
dstDir = args.destinationFolder
if dstDir != None:
	if not dstDir.endswith("/"):
		dstDir += "/"
	if not os.path.isdir(dstDir):
		print "Error. The path to destination directory isn't a directory."
		sys.exit()

#Cannot be verbose and quiet at the same time ;)
if args.quiet:
	args.verbosity = False

#Create the library
lib = Library(srcDir, dstDir, args.maxParseBook, args.verbosity, args.quiet, args.populateDB)

#Print statistics about parsed books
if args.stats:
	lib.printStats()

	