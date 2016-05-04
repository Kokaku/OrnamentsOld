#!/usr/bin/python
import argparse
import sys
import os

parser = argparse.ArgumentParser(description='Process scan pages to extract ornaments.')
parser.add_argument('sourceFile', type=str, help='Source file containing answers')
parser.add_argument('sourceFolder', type=str, help='Source folder of images')
args = parser.parse_args()

#Check that the given source folder is a folder
srcDir = args.sourceFolder
if not srcDir.endswith("/"):
	srcDir += "/"
if not os.path.isdir(srcDir):
	print "Error. The path to source directory isn't a directory."
	sys.exit()

srcFile = args.sourceFile
if not os.path.isfile(srcFile):
	print "Error. The path to source file isn't a file."
	sys.exit()

yes = srcDir+"yes/"
no = srcDir+"no/"
positive = 0
negative = 0
for filename in os.listdir(yes):
	if os.path.isfile(yes+filename) and (filename.endswith(".tif") or filename.endswith(".jp2")):
		positive += 1
for filename in os.listdir(no):
	if os.path.isfile(no+filename) and (filename.endswith(".tif") or filename.endswith(".jp2")):
		negative += 1

total = positive + negative
nbrFiles = 0
truePositive = 0
falseNefative = 0
with open(srcFile) as f:
	for line in f.readlines():
		filename = line.rstrip()
		nbrFiles += 1
		if os.path.isfile(yes+filename):
			truePositive += 1
		else:
			falseNefative += 1
			print "file not present: {0}".format(filename)


print "Selectivity: {0:0.2f}%".format((positive*100.0)/total)
if nbrFiles != 0:
	print "True positive: {0:0.2f}%".format((truePositive*100.0)/nbrFiles)
	print "False positive: {0:0.2f}%".format((falseNefative*100.0)/nbrFiles)
	print "True negative: {0:0.2f}%".format(((negative - falseNefative)*100.0)/(total - nbrFiles))
	print "False negative: {0:0.2f}%".format(((positive - truePositive)*100.0)/(total - nbrFiles))
else:
	print "No file expected, thus 100%"
	