import urllib.request
import urllib.parse
import json

class Wikipedia:
	api_url = "https://en.wikipedia.org/w/api.php?%s"

	def __init__(self, query, count):
		self.bundle = []

		result = self._search(query)
		pages = self._get_pages(result, count)

		for p, r in pages:
			result = self._categorize(p)
			categories = self._get_categories(result)
			page = {}
			page["name"] = p
			page["redirect"] = r
			page["categories"] = categories
			page["content"] = self._get_extract(p)
			self.bundle.append(page)

	def results(self):
		return self.bundle

	def _get_pages(self, response, count):
		result = response["query"]["search"]
		pages = []
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

	def _get_extract(self, page_name):
		result = self._extract(page_name)
		pageobjects = result["query"]["pages"]
		pagenum = next(iter(pageobjects))
		data = pageobjects[pagenum]
		return data["extract"]

	def _search(self, query):
		params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'list': 'search', 'srprop': 'redirecttitle', 'srsearch': query})
		url = Wikipedia.api_url	% params
		return self.__call_api(params)

	def _categorize(self, page_name):
		params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'prop': 'categories', 'clshow': '!hidden', 'cllimit': '100', 'titles': page_name})
		return self.__call_api(params)

	def _extract(self, page_name):
		params = urllib.parse.urlencode({'format': 'json', 'action': 'query', 'prop': 'extracts', 'exintro': '', 'explaintext': '', 'titles': page_name})
		return self.__call_api(params)

	def __call_api(self, params):
		url = Wikipedia.api_url	% params
		with urllib.request.urlopen(url) as f:
			return json.loads(f.read().decode('utf-8'))

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