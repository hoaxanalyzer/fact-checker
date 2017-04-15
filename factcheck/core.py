from . import sources
import string

import logging

import enchant

## NLTK
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem import SnowballStemmer
import nltk
from nltk import ne_chunk, pos_tag, word_tokenize
from nltk.tree import Tree

########################################
##
##  Number code meaning
##
##  0 : Unrelated
##  1 : Hoax
##  2 : Fact
##  3 : Unknown
##  7 : Hoax contained sentences
##	8 : Neutral sentences, probably facts
##  9 : Fact in some claim
##
########################################

class WikipediaCheck:
	wordnet = WordNetLemmatizer()
	snowball = SnowballStemmer("english")

	# TO-DO: Need more list of hoax category
	hoax_category = ['pseudoscience']

	# TO-DO: Synonyms
	synonyms_death = ['died', 'dead', 'death', 'passed', 'gone', 'deceased', 'killed']
	synonyms_clarify = ['is', 'are', 'was', 'were', 'isn', 'aren', 'weren']
	synonyms_negation = ['not', 't', 'don', 'cant', 'cannot', 'won', 'isn', 'aren', 'weren']
	synonyms_assumption = ['if', 'might', 'considered']

	def __init__(self, query):
		logging.info("Start init Wikipedia object")
		self.query = self._clean_query(query.lower()).rstrip()
		self.query_stop = self._stop_query(self.query)
		logging.info("Start stem")
		self.query_stemmed = self._stem_query(self.query_stop)
		logging.info("Finish stem")
		self.query_clean = self._sanitize_query(self.query_stemmed)

		self.properties_bne = self._get_basic_ne(self.query_stop)

		self.about_death = False
		self.about_clarify = False
		logging.info("Finish init Wikipedia object")

	def check(self):
		logging.info("Start checking")
		cl = self.query
		ne = self.properties_bne
		le = self._stop_query(cl).split()
		st = self._the_stops(cl).split()

		logging.info("Finish init checking")
		negate = False
		if self.__is_intersect(WikipediaCheck.synonyms_negation, (self.query).split()):
			negate = True
		logging.info("Finish search negation words")

		if (len(self.query_clean.split()) < 4) or \
			(len(ne) != 0 and len(le) <= 10 and len(st) <= 4):
			logging.info("Starting...")
			quer = self._build_query()
			print("Q: " + quer)
			logging.info("Finish build query")
			wiki = sources.Wikipedia(quer, 3)
			self.result = wiki.results()
			logging.info("OK, getting results page from Wiki")

			if (len(self.result) > 0):
				logging.info("Calculations")
				fact_claims = []
				found_page = False

				page = wiki.get_meta(self.result[self._get_best_title(self.result)])

				logging.info("Start Check Category X")
				ccat = self._check_category(page)
				logging.info("Finish Check Category")
				# print(ccat)
				if ccat[0] < 3:
					return ccat + (negate,)
				if ccat[0] == 9:
					fact_claims.extend(ccat[1])
				## No conclusion, check content
				logging.info("No Conlculsion, Check content")
				ccon = self._check_content(page)
				if ccon[0] == 8 or ccon[0] == 7:
					return ccon + (negate,)
				found_page = True

				if len(fact_claims) != 0:
					return (2, 'The subject is ' + ', '.join(fact_claims)) + (negate,)

		return (3, 'No conclusion') + (negate,)

	def _build_query(self):
		base = self.query_stop

		querywords = self.query_stemmed.split()
		death_syn = self.__intersect(querywords, WikipediaCheck.synonyms_death)
		death_about = (len(death_syn) > 0)
		if death_about:
			death_idx = querywords.index(death_syn[0])
			self.about_death = True
			ne = ""
			if death_idx - 2 >= 0:
				ne += querywords[death_idx - 2]
			if death_idx - 1 >= 0:
				ne += " " + querywords[death_idx - 1]
			return ne

		querywords = self.query.split()
		clarify_syn = self.__intersect(querywords, WikipediaCheck.synonyms_clarify)
		clarify_about = (len(clarify_syn) > 0)
		if clarify_about:
			clarify_idx = querywords.index(clarify_syn[0])
			self.about_clarify = True
			ne = ""
			if clarify_idx - 2 >= 0:
				ne += querywords[clarify_idx - 2]
			if clarify_idx - 1 >= 0:
				ne += " " + querywords[clarify_idx - 1]
			if len(querywords) <= 3 and clarify_idx + 1 < len(querywords):
				ne += " " + querywords[clarify_idx + 1]
			return ne

		## Fallback
		basewords = base.split()
		return ' '.join(basewords[:2])

	def _stem_query(self, query):
		querywords = query.split()
		## Stemming
		stemmed = []
		for word in querywords:
			stemmed.append(WikipediaCheck.wordnet.lemmatize(word))
		# Recompile query
		result = ' '.join(stemmed)
		return result

	def _clean_query(self, sentence):
		for char in string.punctuation:
		    sentence = sentence.replace(char, ' ')
		return sentence

	def _stop_query(self, query):
		stops = set(stopwords.words("english"))
		word_list = word_tokenize(query)
		return ' '.join([word for word in word_list if ((word not in stops) or word == "won")])

	def _sanitize_query(self, query):
		querywords = query.split()
		## Death related
		resultwords = [word for word in querywords if word.lower() not in WikipediaCheck.synonyms_death]
		# Recompile query
		result = ' '.join(resultwords)
		return result

	def _the_stops(self, sentence):
		stops = set(stopwords.words("english"))
		word_list = word_tokenize(sentence)
		return ' '.join([word for word in word_list if word in stops])

	def _get_basic_ne(self, sentence):
		words = sentence.split()
		ne_prob = []
		for word in words:
			if not endict.check(word):
				ne_prob.append(word)
		return ne_prob

	def _get_best_title(self, pages):
		logging.info("Start get best title")
		querywords = self.query_stemmed.split()
		highest_score = 0
		idx = 0
		count = 0
		for page in pages:
			logging.info("Cekin page: " + str(page))
			pagename = self._clean_query(page["name"]).split()
			in_page = self.__intersect(querywords, [x.lower() for x in pagename])
			score = len(in_page) / len(pagename)
			logging.info("Gettin' Score")
			if score > highest_score:
				highest_score = score
				idx = count
			if page["redirect"] != None:
				logging.info("Cekin redirect: " + page["redirect"])
				rediname = self._clean_query(page["redirect"]).split()
				re_page = self.__intersect(querywords, [x.lower() for x in rediname])
				rscore = len(re_page) / len(rediname)
				logging.info("Gettin' Score")
				if rscore > highest_score:
					highest_score = rscore
					idx = count
			count += 1
		logging.info("Finish get best title")
		return idx

	def _check_title(self, page):
		## Still basic checking, more advance method needed
		querywords = self.query_stemmed.split()
		in_page = self.__is_intersect(querywords, [x.lower() for x in self._clean_query(page["name"]).split()])

		try:
			in_redirect = self.__is_intersect(querywords, [x.lower() for x in self._clean_query(page["redirect"]).split()])
		except:
			in_redirect = False

		return in_page or in_redirect

	def _check_category(self, page):
		logging.info("Start Check Category")
		querywords = self.query_stemmed.split()
		querywords_nopage = self.__difference(querywords, [x.lower() for x in page["name"].split()])
		logging.info("Finish Init Check Category")

		correct_claims = []

		for category in page["categories"]:
			logging.info("Iterating on " + category)
			category = category.lower()
			## DEATH
			if self.about_death:
				if "living" in category:
					return (1, page["name"] + ' is still ' + category)
				if "deaths" in category:
					return (2, page["name"] + ' is ' + category)
			else:
				## HOAX
				if category in WikipediaCheck.hoax_category:
					return (1, page["name"] + ' defined as ' + category)
				if "hoaxes" in category:
					return (1, page["name"] + ' defined as ' + category)

		return (3, 'Category is safe')

	def _check_content(self, page):
		base = self.query_clean
		to_check = base.split()
		if len(to_check) >= 2:
			print("To check content: " + str(to_check))
			hoax_word = ['hoax', 'discredited']

			wcontent = page["content"]
			sentences = sent_tokenize(wcontent)
			found_sentences = []

			for sentence in sentences:
				sencheck = self._clean_query(sentence.lower())
				found = []
				for check in to_check:
					if (not check.isdigit()) and check in sencheck:
						found.append(check)
				perct = len(found)/len(to_check)
				if len(self.properties_bne) > 0:
					if (perct >= 0.6) and \
						((len(self.__intersect(self.properties_bne, found))/len(self.properties_bne)) >= 0.3):
						found_sentences.append(sentence)
				else:
					if (perct >= 0.6):
						found_sentences.append(sentence)
			if len(found_sentences) > 0:
				sen_code = 8
				## Check for Hoax related words
				for sentence in found_sentences:
					if (self.__is_intersect(sentence.split(), hoax_word)):
						sen_code = 7
				return (sen_code, found_sentences)

		return (3, 'Nothing in content')

	def __is_intersect(self, list_a, list_b):
		return len(self.__intersect(list_a, list_b)) > 0

	def __intersect(self, list_a, list_b):
		# print(str(list_a) + " <> " + str(list_b))
		return list(set(list_a) & set(list_b))

	def __difference(self, list_a, list_b):
		return list(set(list_a) - set(list_b))


endict = enchant.Dict("en_US")

def get_postag(sentence):
	text = nltk.word_tokenize(sentence)
	return nltk.pos_tag(text)

def get_basic_ne(sentence):
	words = sentence.split()
	ne_prob = []
	for word in words:
		if not endict.check(word):
			ne_prob.append(word)
	return ne_prob

queries = ["Canned food contaminated with HIV in Thailand",
"King Jong Nam killed in Malaysia",
"A massive disc-shaped UFO was spotted in Malaysia.",
"A photograph shows a group of underappreciated Vietnam veterans",
"Lin Dan sent a bromantic letter to Chong Wei",
"Hup Seng biscuits are made from plastic",
"Some guy was selling fake zam-zam water in Malacca",
"NTUC FairPrice $100 coupon Singapore",
"Lee Kuan Yew death",
"Terrorist attack isis mall orchard road singapore december",
"British £5 notes introduced in 2016 contain traces of beef tallow",
"Dogs and wolves are genetically 99.9% identical",
"A KFC promotion offered Extra Crispy Sunscreen to consumers",
"JFK donated his entire presidential salary to charity",
"A woman became pregnant from viewing a 3D porn film",
"Actor Vin Diesel has died",
"Picking bluebonnets is illegal in Texas",
"Nostradamus predicted the 9/11 attacks on the World Trade Center",
"Singer Beyoncé Knowles was killed in a car crash",
"Pope Francis has endorsed Bernie Sanders for President",
"Donald Trump is related to Adolf Hitler",
"ISIS has issued a fatwa to kill American puppies",
"An asteroid will hit earth on Christmas Eve",
"Sulu officials offer reward for info on Abu Sayyaf",
"Pipe bomb on Ratchadamnoen wounds two",
"Tattoos are banned at all Disney theme parks",
"Americans are immune to the Zika virus.",
"The University of Philliphines adopts Project NOAH",
"Trillanes says still no access to Duterte’s bank records",
"Halmen Valdez sacked by Duterte",
"Alibata was the pre-Spanish national writing script",
"Apolinario Mabini was paralyzed because of syphilis",
"Fillipinos are banned for using facebook November 2011 porn attack",
"A Snowfall in Mindanao Philliphine video",
"WhatsApp Gold is a premium service offered by WhatsApp",
"Actor Jack Black passed away in June 2016.",
"Search engine Google manipulated results in favor of Hillary Clinton.",
"A sea monster of giant size was spotted near Antarctica",
"Jordan's King Abdullah II murdered his wife, Queen Rania",
"Actor Nicolas Cage died in a motorcycle accident in July 2016",
"Rodrigo Duterte is the Philippine president",
"Thailand's King Bhumibol Adulyadej dead at 88",
"Vajiralongkorn is Thailand's new King",
"Donald Trump called Abraham Lincoln a traitor",
"Tree Leaf Color is green because of clorofil",
"Linux is developed by Linus Torsvald",
"Imagine Cup is organized by Microsoft",
"Git is developed by Linus Torsvald",
"Microsoft Founder is Bill Gates",
"Steve Jobs and Steve Wozniak is the Apple Founder",
"Macbook Pro is Apple Product",
"Macbook Air is Apple Product",
"iPhone is Apple Product",
"Paris is capital city of France",
"Washington is the capital city of United States",
"London is the capital city of England",
"Barrack Obama Lived in Menteng Jakarta",
"Alfred is Bruce Wayne Assistant",
"Christopher Nolan directed Dunkirk film",
"King Salman visit Malaysia",
"King Salman selfie with Malaysia PM",
"Chevy Chase died of a heart attack on 4 January 2016",
"Actor Sean Penn was killed in January 2016",
"The FDA classified walnuts as drugs",
"Hall of Fame coach John Madden passed away at age 78",
"Actor Jim Carrey has died in a snowboarding accident",
"Marvel Comics writer Stan Lee passed away in May 2016",
"Scientists have created a human-gorilla hybrid called Hurilla"]

proneerror = ["earth is flat",
"earth is round",
"flat earth is real",
"An asteroid will hit earth on Christmas Eve",
"The FDA classified walnuts as drugs",
"Americans are immune to the Zika virus."]

queries = [ "vaccine cause autism",
"Linux is developed by Linus Torsvald",
"Imagine Cup is organized by Microsoft",
"Git is developed by Linus Torsvald",]

def main():
	import time
	d = enchant.Dict("en_US")

	logging.basicConfig(level=logging.DEBUG) 
	logging.getLogger().setLevel(logging.DEBUG)
	
	for query in proneerror:
		start = time.time()
		wc = WikipediaCheck(query)
		print(wc.check())
		stop = time.time()
		print("Elapsed: " + str(stop-start))

if __name__== "__main__":
	main()