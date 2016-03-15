#!/usr/bin/python

class Page:
	def __init__(self, pageId, pageUrl, dpi, seq, admin, orderLabel):
		self.pageId = pageId
		self.pageUrl = pageUrl
		self.dpi = dpi
		self.seq = seq
		self.admin = admin
		self.orderLabel = orderLabel

	def getEntry(self):
		return {"_id" : self.pageId,
					"url" : self.pageUrl,
					"dpi" : self.dpi,
					"seq" : self.seq,
					"type" : self.admin,
					"orderLabel" : self.orderLabel}














