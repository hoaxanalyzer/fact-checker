import urllib.request
import urllib.parse
import json
import logging
import threading
import multiprocessing as mp
from multiprocessing import Queue
import requests

def call_api(params):
	result = requests.get("https://en.wikipedia.org/w/api.php?%s" % params)
	return json.loads(result.content.decode('utf-8'))
	# url = "https://en.wikipedia.org/w/api.php?%s"	% params
	# with urllib.request.urlopen(url) as f:
	# 	return json.loads(f.read().decode('utf-8'))

class Wikipedia:
	api_url = "https://en.wikipedia.org/w/api.php?%s"

	def __init__(self, query, count):
		self.bundle = []

		result = self._search(query)
		pages = self._get_pages(result, count)

		for p, r in pages:
			page = {}
			page["name"] = p
			page["redirect"] = r
			#result = self._categorize(p)
			#categories = self._get_categories(result)
			#page["categories"] = categories
			#page["content"] = self._get_extract(p)
			self.bundle.append(page)

	def results(self):
		return self.bundle

	def get_meta(self, target):
		page = {}
		page["name"] = target["name"]
		page["redirect"] = target["redirect"]

		the_queue = Queue()

		thread_c = mp.Process(target=self._categorize, args=(page["name"], the_queue,))
		thread_c.start()

		thread_e = mp.Process(target=self._extract, args=(page["name"], the_queue,))
		thread_e.start()

		categ = None
		extrc = None

		thread_c.join()
		thread_e.join()

		## HACK HACK HACK
		result1 = json.loads(the_queue.get())
		if result1["data_type"] == "categories": categ = result1
		if result1["data_type"] == "extract": extrc = result1

		result2 = json.loads(the_queue.get())
		if result2["data_type"] == "categories": categ = result2
		if result2["data_type"] == "extract": extrc = result2

		page["categories"] = self._get_categories(categ)
		page["content"] = self._get_extract(extrc)

		# result = self._categorize(page["name"])
		# categories = self._get_categories(result)
		# page["categories"] = categories
		# extracted = self._extract(page["name"])
		# page["content"] = self._get_extract(extracted)
		return page

	def _get_pages(self, response, count):
		pages = []
		## Check for suggestion
		try:
			suggest = response["query"]["searchinfo"]
			pages.append((suggest["suggestion"], None))
		except:
			None
		## Check for result
		result = response["query"]["search"]
		while (len(pages) < count) and (len(pages) != len(result)):
			title = result[len(pages)]["title"]
			try:
				redirect = result[len(pages)]["redirecttitle"]
			except:
				redirect = None
			pages.append((title, redirect))
		return pages

	def _get_categories(self, response):
		categories = []
		try:
			## Handle continue category
			contcat = (response["continue"]["clcontinue"].split("|"))[1].replace("_", " ")
			categories.append(contcat)
		except:
			None
		## Handle other category
		pageobjects = response["query"]["pages"]
		pagenum = next(iter(pageobjects))
		data = pageobjects[pagenum]
		raw_categories = data["categories"]
		for cat in raw_categories:
			categories.append(cat["title"].split(":")[1])
		return categories

	def _get_extract(self, extracted):
		result = extracted
		pageobjects = result["query"]["pages"]
		pagenum = next(iter(pageobjects))
		data = pageobjects[pagenum]
		return data["extract"]

	def _search(self, query):
		# params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'list': 'search', 'srprop': 'redirecttitle', 'srinfo':'suggestion', 'srsearch': query})
		params = 'format=json&action=query&list=search&srprop=redirecttitle&srinfo=suggestion&srsearch=' + query
		return call_api(params)

	def _categorize(self, page_name, queue_out):
		logging.info("Starting get data categorize...")
		# params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'prop': 'categories', 'clshow': '!hidden', 'cllimit': '100', 'redirects':'', 'titles': page_name})
		params = 'format=json&action=query&prop=categories&clshow=!hidden&cllimit=100&redirects=&titles=' + page_name
		result = call_api(params)
		result["data_type"] = "categories"
		# return result
		queue_out.put(json.dumps(result))
		logging.info("Finish get data categorize...")

	def _extract(self, page_name, queue_out):
		logging.info("Starting get data extract...")
		# params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'prop': 'extracts', 'exintro': '', 'explaintext': '', 'redirects':'', 'titles': page_name})
		params = 'format=json&action=query&prop=extracts&exintro=&explaintext=&redirects=&titles=' + page_name
		result = call_api(params)
		result["data_type"] = "extract"
		# return result
		queue_out.put(json.dumps(result))
		logging.info("Finish get data extract...")

def get_postag(sentence):
	text = nltk.word_tokenize(sentence)
	return nltk.pos_tag(text)

def main():
	wiki = Wikipedia('ahok governor jakarta', 1)
	# wiki = Wikipedia('ahok muslim', 1)
	# wiki = Wikipedia('jokowi chinese', 1)
	# wiki = Wikipedia('anies', 1)
	# wiki = Wikipedia('donald trump president united states', 1)
	# wiki = Wikipedia('flat earth', 1)
	# wiki = Wikipedia('earth round', 1)
	res = wiki.results()
	print(res)

if __name__== "__main__":
	main()