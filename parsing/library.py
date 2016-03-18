#!/usr/bin/python
from multiprocessing import Pool
import os
import sys
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

def processBook(args):
	return Book(*args)

class Library:

	def __init__(self, srcDir, dstDir, numThread, maxParseBook, verbosity, quiet, dbUrl, dbUser, dbPassword):
		self.srcDir = srcDir
		books = list()

		# Read all books contained in the library
		for filename in os.listdir(srcDir):
			#Only zipped files are considered as book
			if zipfile.is_zipfile(srcDir+filename):
				book = [filename, srcDir+filename, dstDir, verbosity, dbUrl, dbUser, dbPassword]
				books.append(book)

			if maxParseBook != None and bookToProccessed >= maxParseBook:
				break

		threads = Pool(numThread if numThread != None else 8)
		self.books = list()
		bookToProccess = len(books)
		for book in enumerate(threads.imap_unordered(processBook, books), 1):
			if not quiet:
				print "Analysed book {0}/{1}".format(book[0], bookToProccess)
				if verbosity:
					print ""
			self.books = book[1]


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
	