#!/usr/bin/python
import argparse
import sys
import os
import shutil
import numpy as np
import cv2
import time
from multiprocessing import Pool
from pymongo import MongoClient
import copy
import json
import uuid

def getCorner(box):
    return [(box[0], box[1]),
    (box[0], box[1]+box[3]),
    (box[0]+box[2], box[1]),
    (box[0]+box[2], box[1]+box[3])]

def isPointInBox(p, box):
    return p[0] >= box[0] and p[0] <= box[0]+box[2] and p[1] >= box[1] and p[1] <= box[1]+box[3]

def intersect(box1, box2):
    corners1 = getCorner(box1)
    corners2 = getCorner(box2)
    for corner in corners1:
        if isPointInBox(corner, box2):
            return True

    for corner in corners2:
        if isPointInBox(corner, box1):
            return True

    return False

def onSameLineOrIntersect(box1, box2):
    if intersect(box1, box2):
        return True
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    if h1 > h2*2 or h2 > h1*2:
        return False

    if y1 - y2 < min(h1, h2)/2 and x1 - x2 < 2*max(w1, w2):
        return True

    return False

def mergeBoxes(box1, box2):
    x = min(box1[0], box2[0])
    y = min(box1[1], box2[1])
    x2 = max(box1[0]+box1[2], box2[0]+box2[2])
    y2 = max(box1[1]+box1[3], box2[1]+box2[3])

    return [x, y, x2-x, y2-y]

def getBoxes(img, margin, minSizeBeforeMerge, minSizeAfterMerge):
    boxes = []

    contours, hierarchy = cv2.findContours(img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    imSize = img.shape
    for cnt in contours:
        rect = cv2.boundingRect(cnt)

        if rect[2] < imSize[0]*0.99 and rect[3] < imSize[1]*0.99 and \
            (rect[2] >= minSizeBeforeMerge or rect[3] >= minSizeBeforeMerge):
            rect = [rect[0]-margin , rect[1]-margin, rect[2]+2*margin, rect[3]+2*margin]
            addBox(boxes, rect)

    for box in boxes:
        if box[2] < minSizeAfterMerge and box[3] < minSizeAfterMerge:
            boxes.remove(box)

    return boxes

def addBox(boxes, rect):
    addBoxWithFun(boxes, rect, intersect)

def addBoxWithFun(boxes, rect, intersectFun):
    hasIntersect = True
    while hasIntersect:
        hasIntersect = False
        for box in boxes:
            if intersectFun(box, rect):
                rect = mergeBoxes(box, rect)
                boxes.remove(box)
                hasIntersect = True
    boxes.append(rect)

def getApproxTextSize(filename, imgSize, dbUrl, dbUser, dbPassword):
    avgCharPerLine = 0
    splitFilename = filename.split('-')
    if splitFilename[0] == 'bookm' and len(splitFilename) == 2:
        ids = splitFilename[1].split('_')
        if(len(ids) == 2):
            dbClient = MongoClient(dbUrl)
            if args.dbUser != None and args.dbPassword != None:
                dbClient.ornaments.authenticate(dbUser, dbPassword, source='admin')
            res = dbClient.ornaments.books.find({"_id": ids[0]})
            if res.count() >= 1:
                pageId = int(ids[1].split('.')[0])
                try:
                    avgCharPerLine = res[0]['pages'][pageId]['avgCharPerLine']
                except:
                    avgCharPerLine = 0
                    #print "warning no page: {0} {1}".format(pageId, filename)

                if avgCharPerLine < 20:
                    avgCharPerLine = 0
                    for page in res[0]['pages']:
                        avgCharPerLine += page['avgCharPerLine']
                    avgCharPerLine /= len(res[0]['pages'])

            dbClient.close()

    if avgCharPerLine < 20:
        #print "warning, less than 20 char per line {0}: {1}".format(avgCharPerLine, filename)
        avgCharPerLine = 20

    return imgSize[1]/avgCharPerLine

def processImage(imagePath, filename, dstDir, filterSize, dbUrl, dbUser, dbPassword, debugLevel):
    img = cv2.imread(imagePath,0)

    filterWidth = filterSize if filterSize%2==1 else filterSize+1
    median = cv2.medianBlur(img, filterWidth)

    avgColor = np.sum(median)/(img.shape[0]*img.shape[1])
    if avgColor != 255:
        median = cv2.medianBlur(median, filterWidth)
        avgColor = np.sum(median)/(img.shape[0]*img.shape[1])

    if avgColor == 255:
        return [img.shape, []]
    else:
        imSize = img.shape
        fileNameWithoutExt = filename.split('.')[0]
        fileExt = filename.split('.')[1]
        if debugLevel > 1:
            dstDir = dstDir + fileNameWithoutExt+'/'
            os.makedirs(dstDir)
            cv2.imwrite(dstDir+'page.'+fileExt, img)
            cv2.imwrite(dstDir+'median.'+fileExt, median)

        if not filename.endswith('.tif') :
            thresSize = min(imSize) / 6
            thresSize = thresSize if thresSize%2 == 1 else thresSize+1
            median = cv2.adaptiveThreshold(median,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,thresSize,2)
            img = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,thresSize,2)
            if debugLevel > 1:
                cv2.imwrite(dstDir+'median2.'+filename.split('.')[1], median)
                cv2.imwrite(dstDir+'page2.'+filename.split('.')[1], img)

        
        approxTextSize =  getApproxTextSize(filename, imSize, dbUrl, dbUser, dbPassword)
        medianBoxes = getBoxes(median, filterWidth/4, 0, 0)
        vanillaBoxes = getBoxes(copy.copy(img), 20, 1.5*approxTextSize, 1.5*approxTextSize)

        ornamentBoxes = []
        for mBox in medianBoxes:
            if abs(1-mBox[2]/float(mBox[3])) > 0.1 or mBox[2] < imSize[0]/20 or mBox[0] > imSize[0]/4:
                hasIntersect = True
                vBoxes = copy.copy(vanillaBoxes)
                while hasIntersect:
                    hasIntersect = False
                    for vBox in vBoxes:
                        if intersect(mBox, vBox):
                            mBox = mergeBoxes(mBox, vBox)
                            vBoxes.remove(vBox)
                            hasIntersect = True

            addBox(ornamentBoxes, mBox)


        tmpBoxes = ornamentBoxes
        ornamentBoxes = []
        for box in tmpBoxes:
            addBoxWithFun(ornamentBoxes, box, onSameLineOrIntersect)

        #for box in ornamentBoxes:
        #    x, y, w, h = box

        if debugLevel > 0:
            colorImg = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            for box in ornamentBoxes:
                x, y, w, h = box
                cv2.rectangle(colorImg, (x, y), (x+w, y+h), (255, 0, 0), 10)

            cv2.imwrite(dstDir+filename, colorImg)

        if debugLevel > 1:
            colorImg = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            for box in medianBoxes:
                x, y, w, h = box
                cv2.rectangle(colorImg, (x, y), (x+w, y+h), (255, 0, 0), 10)

            cv2.imwrite(dstDir+'medianBoxes.'+fileExt, colorImg)

            colorImg = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            for box in vanillaBoxes:
                x, y, w, h = box
                cv2.rectangle(colorImg, (x, y), (x+w, y+h), (255, 0, 0), 10)

            cv2.imwrite(dstDir+'vanillaBoxes.'+fileExt, colorImg)

            colorImg = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            for box in getBoxes(copy.copy(img), 10, 2*filterWidth, 2*filterWidth):
                x, y, w, h = box
                cv2.rectangle(colorImg, (x, y), (x+w, y+h), (255, 0, 0), 10)

            cv2.imwrite(dstDir+'noMargin.'+fileExt, colorImg)

            colorImg = cv2.cvtColor(img,cv2.COLOR_GRAY2RGB)
            tmp = copy.copy(img)
            contours, hierarchy = cv2.findContours(tmp,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            for box in map(lambda cnt:cv2.boundingRect(cnt), contours):
                x, y, w, h = box
                cv2.rectangle(colorImg, (x, y), (x+w, y+h), (255, 0, 0), 10)

            cv2.imwrite(dstDir+'contours.'+fileExt, colorImg)
            cv2.imwrite(dstDir+'test.'+fileExt, tmp)

        ornamentBoxes = map(lambda box:{
            "x":max(0, box[0]),
            "y":max(0, box[1]),
            "w":min(box[2], imSize[0]),
            "h":min(box[3], imSize[1])}, ornamentBoxes)
        return [imSize, ornamentBoxes]

def createJson(dbUrl, dbUser, dbPassword, bookId, pagesSize, boxes):
    dbClient = MongoClient(dbUrl)
    if dbUser != None and dbPassword != None:
        try:
            dbClient.ornaments.authenticate(dbUser, dbPassword, source='admin')
        except:
            print "Error, connection to the database is impossible. Most probably the url, user or password is wrong."
            sys.exit()

    books = dbClient.ornaments.books
    for book in books.find({'_id' : bookId}):
        dhCanvasBook = {}
        dhCanvasBook['uuid'] = str(uuid.uuid4())
        dhCanvasBook['id'] = book['_id']
        dhCanvasBook['metadata'] = {"titles" : book["titles"],
                "author" : book["author"],
                "publishers" : book["publishers"],
                "publishedDate" : book["publishedDate"],
                "pageCount" : book["pageCount"],
                "genre" : book["genre"],
                "lang" : book["lang"],
                "dimensions" : book["dimensions"],
                "notes" : book["notes"]}

        dhCanvasPages = []
        for page in book['pages']:
            if page['_id'] in pagesSize:
                dhCanvasPage = {}
                dhCanvasPage['sequenceNumber'] = int(page['_id'])
                dhCanvasPage['id'] = page['_id']
                dhCanvasPage['url'] = page['url'][:-24]
                pageSize = pagesSize[page['_id']]
                dhCanvasPage['width'] = pageSize[0]
                dhCanvasPage['height'] = pageSize[1]
                dhCanvasPage['metadata'] = {"dpi" : page['dpi'],
                            "seq" : page['seq'],
                            "type" : page['type'],
                            "orderLabel" : page['orderLabel'],
                            "avgCharPerLine" : page['avgCharPerLine']}
                dhCanvasPage['segments'] = boxes[page['_id']]

                dhCanvasPages.append(dhCanvasPage)


        dhCanvasBook['pages'] = dhCanvasPages

        jsonFile = open(dstDir+book['_id']+".json", "w")
        jsonFile.write(json.dumps(dhCanvasBook, indent=4, sort_keys=True))
        jsonFile.close()

def processImageArgs(args):
        return processImage(*args)


def processBook(args):
    splitBookFolder = args[1].split('-')
    if len(splitBookFolder) >= 2:
        boxes = {}
        pagesSize = {}
        for arg in args[0]:
            pagename = arg[1].split('.')[0]
            pageData = processImageArgs(arg)
            pagesSize[pagename] = pageData[0]
            boxes[pagename] = pageData[1]

        createJson(args[2], args[3], args[4], splitBookFolder[1], pagesSize, boxes)

def getImageJobs(srcDir, sourceFile, files, dbUrl, dbUser, dbPassword, debugLevel) :
    images = list()
    for filename in os.listdir(srcDir):
        if filename.endswith('.jp2') or filename.endswith('.tif'):
            if sourceFile == None or filename in files:
                imagePath = srcDir+filename
                image = [imagePath, filename, dstDir, filterSize, dbUrl, dbUser, dbPassword, debugLevel]
                images.append(image)
                #processImageArgs(image)
    return images

parser = argparse.ArgumentParser(description='Process scan pages to extract ornaments.')
parser.add_argument('sourceFolder', type=str, help='Source folder of images')
parser.add_argument('destinationFolder', type=str, help='Destination folder for images')
parser.add_argument('dbUrl', type=str, help='Populate the database with parsed data at the given address')
parser.add_argument('-u', '--user', action="store", dest='dbUser', type=str, nargs='?', help='Database user')
parser.add_argument('-p', '--password', action="store", dest='dbPassword', type=str, nargs='?', help='Database password')
parser.add_argument('-t', '--thread', action="store", dest='numThread', type=int, nargs='?', help='Number of thread to proccess data')
parser.add_argument('-s', '--size', action="store", dest='filterSize', type=int, nargs='?', help='Filter size')
parser.add_argument('-f', '--srcFile', action="store", dest='sourceFile', type=str, nargs='?', help='Source file that contain filename to process (filter other files)')
parser.add_argument('-pm', '--pageMode', help='Activate page mode', action='store_true')
parser.add_argument('-d', '--debug', action="store", dest='debug', type=int, nargs='?', help='Debug level')
args = parser.parse_args()

if args.sourceFile != None:
    srcFile = args.sourceFile
    if not os.path.isfile(srcFile):
        print "Error. The path to source file isn't a file."
        sys.exit()

    files = []
    with open(srcFile) as f:
        files = f.readlines()
        files = map(str.strip, files)
else:
    files = []

#Check DB connection
dbUrl = None
if args.dbUrl != None:
    if len(args.dbUrl.split(':')) == 1:
        dbUrl = 'mongodb://{0}:27017'.format(args.dbUrl)
    else:
        dbUrl = 'mongodb://{0}'.format(args.dbUrl)

    dbClient = MongoClient(dbUrl)
    if args.dbUser != None and args.dbPassword != None:
        try:
            dbClient.ornaments.authenticate(args.dbUser, args.dbPassword, source='admin')
        except:
            print "Error, connection to the database is impossible. Most probably the url, user or password is wrong."
            sys.exit()

    try:
        dbClient.close()
    except:
        print "Error, connection to the database is impossible. Most probably the url is wrong."
        sys.exit()


filterSize = args.filterSize
if filterSize == None:
        filterSize = 65

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

numThread = args.numThread
tStart = time.time()
if os.path.exists(dstDir):
    shutil.rmtree(dstDir)
os.makedirs(dstDir)

if args.pageMode:
    images = getImageJobs(srcDir, args.sourceFile, files, dbUrl, args.dbUser, args.dbPassword, args.debug)
else:
    books = list()
    for bookFolder in os.listdir(srcDir):
        bookPath = srcDir+bookFolder+"/"
        if os.path.isdir(bookPath):
            images = getImageJobs(bookPath, args.sourceFile, files, dbUrl, args.dbUser, args.dbPassword, args.debug)
            books.append([images, bookFolder, dbUrl, args.dbUser, args.dbPassword])
            #processBook([images, bookFolder, dbUrl, args.dbUser, args.dbPassword])

#sys.exit()
tMid = time.time()
print "time mid: {0}".format(tMid - tStart)
threads = Pool(numThread if numThread != None else 8)

if args.pageMode:
    imNum = len(images)
    for image in enumerate(threads.imap_unordered(processImageArgs, images), 1):
       print "Analysed images {0}/{1}".format(image[0], imNum)
else:
    bookNum = len(books)
    for book in enumerate(threads.imap_unordered(processBook, books), 1):
	   print "Analysed books {0}/{1}".format(book[0], bookNum)

tEnd = time.time()
print "time: {0}".format(tEnd - tStart)




