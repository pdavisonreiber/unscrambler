import argparse
import os
import datetime
import yaml
from PyPDF2 import PdfReader, PdfWriter

def cropPageLeft(page):
	width = page.mediabox.lower_right[0]
	height = page.mediabox.upper_left[1]
	
	if width > height:
		page.cropbox.lower_left = (0, 0)
		page.cropbox.lower_right = (width/2, 0)
		page.cropbox.upper_left = (0, height)
		page.cropbox.upper_right = (width/2, height)
	else:
		page.cropbox.lower_left = (0, height/2)
		page.cropbox.lower_right = (width, height/2)
		page.cropbox.upper_left = (0, height)
		page.cropbox.upper_right = (width, height)
		

def cropPageRight(page):
	width = page.mediabox.lower_right[0]
	height = page.mediabox.upper_left[1]
	
	if width > height:
		page.cropbox.lower_left = (width/2, 0)
		page.cropbox.lower_right = (width, 0)
		page.cropbox.upper_left = (width/2, height)
		page.cropbox.upper_right = (width, height)
	else:
		page.cropbox.lower_left = (0, 0)
		page.cropbox.lower_right = (width, 0)
		page.cropbox.upper_left = (0, height/2)
		page.cropbox.upper_right = (width, height/2)
	
	
def splitPDF(document, pagesPerDocument):
	numberOfPages = len(document.pages)
	
	if numberOfPages % pagesPerDocument != 0:
		raise Exception("Number of pages in file not divisible by " + str(pagesPerDocument) + ".")
		
	writers = [PdfWriter() for _ in range(numberOfPages // pagesPerDocument)]
	
	for i in range(numberOfPages):
		writers[i // pagesPerDocument].add_page(document.pages[i])
		
	return writers
		
		
def splitA3Booklet(document1, document2, pagesPerDocument):
	numPages = len(document1.pages)
	
	if numPages % pagesPerDocument != 0:
		raise Exception(f"Number of pages not divisible by {pagesPerDocument}.")
	
	page = document1.pages[0]
	width = page.mediabox.lower_right[0]
	height = page.mediabox.upper_left[1]
	numDocs = numPages // pagesPerDocument
	
	arraysOfPages1 = [[document1.pages[i] for i in range(k * pagesPerDocument, (k + 1) * pagesPerDocument)] for k in range(numDocs)]
	arraysOfPages2 = [[document2.pages[i] for i in range(k * pagesPerDocument, (k + 1) * pagesPerDocument)] for k in range(numDocs)]
		
	outputWriter = PdfWriter()
	
	for i in range(numDocs):
		writer = PdfWriter()
		
		for j in range(pagesPerDocument):
			cropPageLeft(arraysOfPages1[i][j])
			cropPageRight(arraysOfPages2[i][j])
			
			if j % 2 == 0:
				writer.insert_page(arraysOfPages1[i][j])
				writer.add_page(arraysOfPages2[i][j])
			if j % 2 == 1:
				writer.add_page(arraysOfPages1[i][j])
				writer.insert_page(arraysOfPages2[i][j])
			
		for page in writer.pages:
			outputWriter.add_page(page)
			
	return outputWriter
	
	
def scramble(document, pagesPerDocument, split=False, doublePage=False, doublePageReversed=False):
	numberOfPages = len(document.pages)
	
	if numberOfPages % pagesPerDocument != 0:
		raise Exception("Number of pages in file not divisible by " + str(pagesPerDocument) + ".")
	
	if doublePageReversed:
		writers = splitPDF(document, pagesPerDocument * 2)
	else:
		writers = splitPDF(document, pagesPerDocument)
	
	if doublePage:
		if numberOfPages % 2 != 0:
			raise Exception("Number of pages per document is not even.")
	
		outputWriters = [PdfWriter() for _ in range(pagesPerDocument // 2)]
		
		for writer in writers:
			outputWriters[0].add_page(writer.pages[0])
			outputWriters[0].add_page(writer.pages[len(writer.pages) - 1])
			
			for i in range(1, len(writer.pages) // 2):
				outputWriters[i].add_page(writer.get_page(2*i - 1))
				outputWriters[i].add_page(writer.get_page(2*i))
			
	elif doublePageReversed:
		outputWriters = [PdfWriter() for _ in range(pagesPerDocument)]
		
		for i in range(pagesPerDocument):
			outputWriters[i].add_page(writers[0].pages[2*i])
		for writer in writers[1:]:
			for i in range(pagesPerDocument):
				outputWriters[i].add_page(writer.pages[2*i])
				outputWriters[i].add_page(writer.pages[2*i + 1])
		for i in range(pagesPerDocument):
			outputWriters[i].add_page(writers[0].pages[2*i + 1])
				
	else:
		outputWriters = [PdfWriter() for _ in range(pagesPerDocument)]
		
		for writer in writers:
			for i in range(len(writer.pages)):
				outputWriters[i].add_page(writer.pages[i])
		
	
			
	if split:
		return outputWriters
	else:
		finalWriter = PdfWriter()
	
		for outputWriter in outputWriters:
			for page in [outputWriter.pages[i] for i in range(len(outputWriter.pages))]:
				finalWriter.add_page(page)
	
		return finalWriter
	
def saveDocuments(documents, directory):
	os.makedirs(directory)
	
	for i, document in enumerate(documents):
		filename = os.path.basename(directory) + f"_{i + 1}.pdf"
		filePath = os.path.join(directory, filename)
		
		with open(filePath, "wb") as output:
			document.write(output)
	
	
		
def unscramble(filename, pagesPerDocument, isBooklet, split, rearrange, doublePage, doublePageReversed):
	pdf = open(filename, "rb")
	document = PdfReader(pdf)
	document2 = PdfReader(pdf)
	
	directory = os.path.splitext(filename)[0]
	print("directory:", directory)
	
	if rearrange:
		if isBooklet:
			document = splitA3Booklet(document, document2, pagesPerDocument)
			pagesPerDocument *= 2
		
		if split:
			documents = scramble(document, pagesPerDocument, split=True, doublePageReversed=doublePageReversed)
			saveDocuments(documents, directory)
		else:
			if doublePage and doublePageReversed:
				raise Exception("The -d and -dr options cannot both be selected.")
			elif doublePage:
				document = scramble(document, pagesPerDocument, doublePage=doublePage)
			elif doublePageReversed:
				document = scramble(document, pagesPerDocument, doublePageReversed=doublePageReversed)
			else:
				document = scramble(document, pagesPerDocument)
			
			with open(f"{filenamePrefix}_output.pdf", "wb") as output:
				document.write(output)
			
	elif isBooklet:
		document = splitA3Booklet(document, document2, pagesPerDocument)
		pagesPerDocument *= 2
		
		if split:
			documents = splitPDF(document, pagesPerDocument)
			saveDocuments(documents, directory)
		else:
			with open(f"{filenamePrefix}_output.pdf", "wb") as output:
				document.write(output)
				
	elif split:
		documents = splitPDF(document, pagesPerDocument)
		saveDocuments(documents, directory)
	else:
		raise Exception("You must select at least one option: -r, -s, or -b.")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("filename")
	parser.add_argument("numpages", type=int, help="The number of pages per document", nargs="?")
	parser.add_argument("-b", "--booklet", action="store_true", help="Use this option if the original is an A3 booklet. Source PDF is expected to be in landscape with the middle pages coming first.")
	parser.add_argument("-s", "--split", action="store_true", help="Use this option if you would like the output to be split into multiple files.")
	parser.add_argument("-r", "--rearrange", action="store_true", help="Use this option to rearrange the pages.")
	parser.add_argument("-d", "--doublePage", action="store_true", help="Use this option to rearrange pages so that double pages stay together. This assumes there is a front and back cover.")
	parser.add_argument("-D", "--doublePageReversed", action="store_true", help="Use this option when unscrambling a document for which the -d option was used.")
	parser.add_argument("-y", "--parseYAML", help="Use when options are being parsed from a YAML file.")

	args = parser.parse_args()
	
	if args.parseYAML:
		with open(args.parseYAML, "r") as yamlFile:
			options = yaml.safe_load(yamlFile.read())
			numpages = options["number_of_pages"]
			booklet = options["booklet"]
			split = options["split"]
			rearrange = options["rearrange"]
			doublePage = options["double_page"]
			doublePageReversed = options["reverse_double_page"]
		unscramble(args.filename, numpages, booklet, split, rearrange, doublePage, doublePageReversed)
	else:
		unscramble(args.filename, args.numpages, args.booklet, args.split, args.rearrange, args.doublePage, args.doublePageReversed)

if __name__ == "__main__":
    main()
