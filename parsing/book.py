#!/usr/bin/python
import zipfile
import sys
import os
import shutil
from PIL import Image
from lxml import etree
from pymongo import MongoClient
from page import Page

# This URL allow to search for books in the Google library
googleBookSearchUrl = "https://www.googleapis.com/books/v1/volumes?q="
# This URL allow to query for a book in the Google library
googleBookUrl = "https://www.googleapis.com/books/v1/volumes/"

class Book:
	def __init__(self, filename, path, dstDir, verbosity, dbUrl, dbUser, dbPassword):
		filename = filename.split('.')[0]
		self.filename = filename
		self.path = path
		self.dstDir = dstDir

		self.initVariables()
		self.bookId = self.filename.split('-')[1]

		if verbosity:
			print filename

		if dstDir != None:
			imDir = dstDir+filename
			if os.path.exists(imDir):
			    shutil.rmtree(imDir)
			os.makedirs(imDir)

		zf = zipfile.ZipFile(path, 'r')
		for zi in zf.infolist():
			self.size += zi.file_size
			if zi.filename.endswith(".jp2"):
				self.handleJp2(zf, zi)
			elif zi.filename.endswith(".tif"):
				self.handleTiff(zf, zi)
			elif zi.filename.endswith(".xml"):
				self.handleXml(zf, zi)

		if verbosity:
			self.printParsedData()
		if dbUrl != None:
			dbClient = MongoClient(dbUrl)
			if dbUser != None and dbPassword != None:
				dbClient.ornaments.authenticate(dbUser, dbPassword, source='admin')
			db = dbClient.ornaments
			self.populateDB(db)
			dbClient.close()

		zf.close()

	def initVariables(self):
		self.size = 0
		self.imSize = 0
		self.jp2Size = 0
		self.xmlSize = 0
		self.numJp2 = 0
		self.numTif = 0
		self.numIm = 0

		self.titles = None
		self.author = None
		self.publishers = None
		self.publishedDate = None
		self.pageCount = None
		self.genre = None
		self.lang = None
		self.dimensions = None
		self.notes = None

		self.pages = list()

	def getSize(self):
		return self.size

	def getImSize(self):
		return self.imSize

	def getJp2Size(self):
		return self.jp2Size

	def getXmlSize(self):
		return self.xmlSize

	def getNumJp2(self):
		return self.numJp2

	def getNumTif(self):
		return self.numTif

	def handleJp2(self, zf, zi):
		self.jp2Size += zi.file_size
		self.numJp2 += 1
		self.handleImage(zf, zi)

	def handleTiff(self, zf, zi):
		self.numTif += 1
		self.handleImage(zf, zi)

	def handleImage(self, zf, zi):
		self.imSize += zi.file_size
		self.numIm += 1
		if self.dstDir != None:
			zf.extract(zi, self.dstDir+self.filename)


	def handleXml(self, zf, zi):
		self.xmlSize += zi.file_size

		if zi.filename == "glr_mods.xml":
			self.parseGlrMods(zf.read(zi.filename))
		elif zi.filename.startswith("BCUL_"):
			self.parseBcul(zf, zf.read(zi.filename))
		#elif zi.filename == "glr_oai_dc.xml":
		#	self.parseGlrOaiDc(zf.read(zi.filename))

	def parseGlrMods(self, strFile):
		metaData = etree.fromstring(strFile)
		self.titles = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "titleInfo"]/*[local-name() = "title"]/text()')
		self.author = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "name"]/*[local-name() = "namePart"]/text()')
		self.publishers = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "originInfo"]/*[local-name() = "publisher"]/text()')
		self.publishedDate = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "originInfo"]/*[local-name() = "dateIssued"]/text()')
		self.genre = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "genre"]/text()')
		self.lang = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "language"]/child::*/text()')
		self.dimensions = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "physicalDescription"]/child::*/text()')
		self.notes = metaData.xpath('//*[local-name() = "mods"]/*[local-name() = "note"]/text()')

	def parseBcul(self, zf, strFile):
		def getFirstOrNone(l):
			if len(l) > 0:
				return l[0]
			return None

		pageXmlId = None
		seq = None
		admin = None
		orderLabel = None
		pageId = None
		orderLabel = None
		dpi = None

		metaData = etree.fromstring(strFile)
		imagesData = metaData.xpath('//*[local-name() = "fileGrp"][@USE="image"]/child::*')
		pagesData = getFirstOrNone(metaData.xpath('//*[local-name() = "div"][@TYPE="volume"]'))
		for imageData in imagesData:
			fileData = getFirstOrNone(imageData.xpath('./child::*'))
			if fileData != None:
				pageFilename = fileData.items()[0][1]
				pageId = pageFilename.split('.')[0]
				try:
					im = Image.open(zf.open(pageFilename))
					dpi = im.info['dpi']
					dpi = (float(dpi[0].numerator)/dpi[0].denominator, float(dpi[1].numerator)/dpi[1].denominator)
				except:
					dpi = None
				pageUrl = "http://dhlabsrv4.epfl.ch/iiif_ornaments/bookm-{0}_{1}/full/full/0/default.jpg".format(self.bookId, pageId)
			pageXmlId = imageData.get("ID")
			seq = imageData.get("SEQ")
			if pageXmlId != None:
				pageData = getFirstOrNone(pagesData.xpath('./child::*/child::*[@FILEID="{0}"]/parent::*'.format(pageXmlId)))
				if pageData != None:
					admin = pageData.get("ADMID")
					orderLabel = pageData.get("ORDERLABEL")
					if admin != None:
						admin = admin.split(" ")

			self.pages.append({"_id" : pageId,
					"url" : pageUrl,
					"dpi" : dpi,
					"seq" : seq,
					"type" : admin,
					"orderLabel" : orderLabel})


	def parseGlrOaiDc(self, strFile):
		metaData = etree.fromstring(zf.read(zi.filename))
		self.titles = metaData.xpath('//*[local-name() = "title"]/text()')
		self.author = metaData.xpath('//*[local-name() = "creator"]/text()')
		self.publishers = metaData.xpath('//*[local-name() = "publisher"]/text()')
		self.publishedDate = metaData.xpath('//*[local-name() = "date"]/text()')
		self.lang = metaData.xpath('//*[local-name() = "language"]/text()')
		self.notes = metaData.xpath('//*[local-name() = "description"]/text()')

	def printParsedData(self):
		print "titles: {0}".format(self.titles)
		print "author: {0}".format(self.author)
		print "publishers: {0}".format(self.publishers)
		print "publishedDate: {0}".format(self.publishedDate)
		print "pageCount: {0}".format(self.pageCount)
		print "genre: {0}".format(self.genre)
		print "lang: {0}".format(self.lang)
		print "dimensions: {0}".format(self.dimensions)
		print "notes: {0}".format(self.notes)

	def populateDB(self, db):
		books = db.books

		search = books.find({"_id": self.bookId})

		if search.count() != 0:
			print "Book {0} has already an entry in the DB.".format(self.bookId)
		else:
			result = books.insert_one({"_id" : self.bookId,
				"titles" : self.titles,
				"author" : self.author,
				"publishers" : self.publishers,
				"publishedDate" : self.publishedDate,
				"pageCount" : self.numIm,
				"genre" : self.genre,
				"lang" : self.lang,
				"dimensions" : self.dimensions,
				"notes" : self.notes,
				"pages" : [page for page in self.pages]})













