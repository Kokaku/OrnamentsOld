#!/usr/bin/python
import os
import zipfile
from pymongo import MongoClient
from book import Book

#Pretty print for file size
def formatSize(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

class Library:
	def __init__(self, srcDir, dstDir, maxParseBook, verbosity, quiet, populateDB, db):
		self.srcDir = srcDir
		self.books = list()

		fileToProccess = len(os.listdir(srcDir))
		fileProccessed = 0
		bookProccessed = 0

		# Read all books contained in the library
		for filename in os.listdir(srcDir):
			if verbosity:
				print filename
			fileProccessed += 1

			#Only zipped files are considered as book
			if zipfile.is_zipfile(srcDir+filename):
				book = Book(filename, srcDir+filename, dstDir, verbosity, populateDB, db)
				self.books.append(book)
				bookProccessed += 1

			if maxParseBook != None and bookProccessed >= maxParseBook:
				print "Maximum number of books have been parsed"
				break

			if not quiet:
				print "Analysed file {0}/{1}".format(fileProccessed, fileToProccess)
				if verbosity:
					print ""

	def getListOfBooks(self):
		return self.books

	def getSize(self):
		libSize = 0
		for book in self.books:
			libSize += book.getSize()

		return libSize

	def getImSize(self):
		libSize = 0
		for book in self.books:
			libSize += book.getImSize()

		return libSize

	def getJp2Size(self):
		libSize = 0
		for book in self.books:
			libSize += book.getJp2Size()

		return libSize

	def getXmlSize(self):
		libSize = 0
		for book in self.books:
			libSize += book.getXmlSize()

		return libSize

	def getNumJp2(self):
		num = 0
		for book in self.books:
			num += book.getNumJp2()

		return num

	def getNumTif(self):
		num = 0
		for book in self.books:
			num += book.getNumTif()

		return num

	def printStats(self):
		print "\nOverall size: {0}".format(formatSize(self.getSize()))
		print "Images size: {0}".format(formatSize(self.getImSize()))
		print "Jpeg2000 size: {0}".format(formatSize(self.getJp2Size()))
		print "XML size: {0}".format(formatSize(self.getXmlSize()))
		print "Number of Jpeg2000: {:,}".format(self.getNumJp2())
		print "Number of TIF: {:,}".format(self.getNumTif())
	