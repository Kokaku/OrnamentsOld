#!/usr/bin/python
import argparse
import sys
import os
import shutil
import numpy as np
import cv2
import time
#from matplotlib import pyplot as plt
from multiprocessing import Pool
from pymongo import MongoClient

def processImage(imagePath, filename, dstDir, factor):
    avgCharPerLine = 0
    splitFilename = filename.split('-')
    if splitFilename[0] == 'bookm' and len(splitFilename) == 2:
    	ids = splitFilename[1].split('_')
    	if(len(ids) == 2):
			dbClient = MongoClient('mongodb://localhost:27017')
			res = dbClient.ornaments.books.find({"_id": ids[0]})
			if res.count() >= 1:
				pageId = int(ids[1].split('.')[0])
				try:
					avgCharPerLine = res[0]['pages'][pageId]['avgCharPerLine']
				except:
					print "warning no page: {0} {1}".format(pageId, filename)

				if avgCharPerLine < 20:
					avgCharPerLine = 0
					for page in res[0]['pages']:
						avgCharPerLine += page['avgCharPerLine']
					avgCharPerLine /= len(res[0]['pages'])

			dbClient.close()

	if avgCharPerLine < 20:
		print "warning: {0}".format(filename)
		avgCharPerLine = 20

    img = cv2.imread(imagePath,0)
    filterWidth = int(img.shape[1]*factor/avgCharPerLine)
    filterWidth = filterWidth if filterWidth%2==1 else filterWidth+1
    median = cv2.medianBlur(img, filterWidth)

    avgColor = np.sum(median)/(img.shape[0]*img.shape[1])
    if avgColor != 255:
        median = cv2.medianBlur(median, filterWidth)
        avgColor = np.sum(median)/(img.shape[0]*img.shape[1])

    #print avgColor
    if avgColor != 255:
    	cv2.imwrite(dstDir+"yes/"+filename, np.concatenate((median, img), axis=1))
    else:
    	cv2.imwrite(dstDir+"no/"+filename, np.concatenate((median, img), axis=1))


def processImageArgs(args):
        return processImage(*args)



parser = argparse.ArgumentParser(description='Process scan pages to extract ornaments.')
parser.add_argument('sourceFolder', type=str, help='Source folder of images')
parser.add_argument('destinationFolder', type=str, help='Destination folder for images')
parser.add_argument('-t', '--thread', action="store", dest='numThread', type=int, nargs='?', help='Number of thread to proccess data')
parser.add_argument('-f', '--factor', action="store", dest='factor', type=float, nargs='?', help='Filter size factor')
args = parser.parse_args()

factor = args.factor
if factor == None:
        factor = 1

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

dstDir += str(factor)+"/"

numThread = args.numThread


tStart = time.time()
images = list()
if os.path.exists(dstDir):
    shutil.rmtree(dstDir)
os.makedirs(dstDir)
os.makedirs(dstDir+"yes")
os.makedirs(dstDir+"no")


for filename in os.listdir(srcDir):
    if filename.endswith('.jp2') or filename.endswith('.tif'):
        imagePath = srcDir+filename
        image = [imagePath, filename, dstDir, factor]
        images.append(image)

tMid = time.time()
print "time mid: {0}".format(tMid - tStart)

imageNum = len(images)
threads = Pool(numThread if numThread != None else 8)
for image in enumerate(threads.imap_unordered(processImageArgs, images), 1):
	print "Analysed image {0}/{1}".format(image[0], imageNum)

tEnd = time.time()
print "time: {0}".format(tEnd - tStart)




