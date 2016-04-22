#!/usr/bin/python
import argparse
import sys
import os
from sets import Set
from random import randint
import shutil

parser = argparse.ArgumentParser(description='Randomly select page amoung books')
parser.add_argument('sourceFolder', type=str, help='Source folder of images')
parser.add_argument('destinationFolder', type=str, help='Destination folder to write results')
parser.add_argument('numElem', type=int, help='Number of elements to be selected')
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
if not dstDir.endswith("/"):
	dstDir += "/"

if os.path.exists(dstDir):
    shutil.rmtree(dstDir)
os.makedirs(dstDir)

numElem = args.numElem

selectedPage = Set()
books = os.listdir(srcDir)
while numElem > 0:
	book = books[randint(0, len(books)-1)]
	bookPath = srcDir+book+"/"
	if os.path.isdir(bookPath):
		images = os.listdir(bookPath)
		image = images[randint(0, len(images)-1)]
		filePath = bookPath+image
		if os.path.isfile(filePath) and (image.endswith(".jp2") or image.endswith(".tif")) and not filePath in selectedPage:
			selectedPage.add(filePath)
			shutil.copyfile(filePath, dstDir+book+"_"+image)
			print filePath
			numElem -= 1