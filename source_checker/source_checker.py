# -*- coding: utf-8 -*-
from pattern.en import ngrams
from pattern.web import Google, SEARCH
from pattern.db import Datasheet
from pattern.db  import pd
from collections import defaultdict
import csv
import string
import collections
import re
import random
import nltk
from nltk.corpus import stopwords
from nltk import ne_chunk, pos_tag, word_tokenize
from pattern.graph import Graph
from itertools import izip
import sys

class SourceChecker(object):

	def __init__(self, text, max_queries = 10, span = 20, threshold = .8):
		self.max_queries = max_queries
		self.span = span
		self.threshold = threshold
		self.text = text
		self.cat_dict = defaultdict(list)
		self.engine = Google(license='AIzaSyCFgnXgb9rcwJspcSeXHo7QHvucgM2nLrI', throttle=0.5, language=None)

	def get_queries(self):
		text = self.text
		beg_quotes = re.findall(r'\"\S', text)
		for each in beg_quotes:
			text = text.replace(each, 'BEGQ' + each[-1])

		end_quotes = re.findall(r'\S\"', text)
		for each in end_quotes:
			text = text.replace(each, each[0] + 'ENDQ')

		text = re.sub('(ENDQ)+', 'ENDQ', text)
		text = re.sub('(BEGQ)+', 'BEGQ', text)
		text = text.replace('--', 'DOUBLEDASH')

		all_ngrams = ngrams(text, n = self.span, punctuation = "", continuous = True)
		stop_words = stopwords.words('english')
		queries = []

		for ngram in all_ngrams:
			num_stop = len([w for w in ngram if w in stop_words])
			stop_score = float(num_stop)/len(ngram)

			chunked = ne_chunk(pos_tag(ngram))
			named_entities = [[w for w, t in elt] for elt in chunked if isinstance(elt, nltk.Tree)]
			num_ent = sum([len(ent_list) for ent_list in named_entities])
			ent_score = float(num_ent)/len(ngram)

			if stop_score < self.threshold and ent_score < self.threshold:
				r_string = self.reconstruct_ngram(ngram)
				if r_string in self.text:
					queries.append(r_string)

		reduction = len(queries)/self.max_queries
		return queries[0::reduction]
		
	def reconstruct_ngram(self, ngram):
		punc_b = ['!', '?', '.', ',', ';', ':', '\'', ')', ']', '}']
		punc_a = ['(', '[', '}', '$']
		ngram = ' '.join(ngram)
		for p in punc_b:
			ngram = ngram.replace(' '+p, p)
		for p in punc_a:
			ngram = ngram.replace(p+' ', p)
		ngram = re.sub('(^| )BEGQ', ' "', ngram)
		ngram = re.sub('ENDQ($| )', '" ', ngram)
		ngram = ngram.replace('DOUBLEDASH', '--')
		return ngram 

	def load_domains(self):
		sources_path = pd('data', 'source_data.csv')
		domain_file = Datasheet.load(sources_path, headers = True)
		for row in domain_file:
			url  = row[1]
			cats = row[2:]
			self.cat_dict[url] = cats

	def pairwise(self, t):
	    it = iter(t)
	    return izip(it,it)

	def get_urls(self, queries):
		domains = defaultdict(list)
		for q in queries:
			q = "\"" + q + "\""
			results = self.engine.search(q)

			for result in results:			
				url = result.url
				domain = self.get_domain(url)
				domains[domain].append(q)	
		return domains

	def get_domain(self, full_url):
		clean_reg= re.compile(r'^((?:https?:\/\/)?(?:www\.)?).*?(\/.*)?$')
		match = re.search(clean_reg, full_url)
		beg, end = match.group(1), match.group(2)
		domain = string.replace(full_url, beg, '')
		domain = string.replace(domain, end, '')
		return domain

	def render_output(self, domains):
		output = defaultdict(list)
		for d,v in domains.items():
			d_cats = [c for c in self.cat_dict[d] if len(c)>0 and len(c.split(' '))<3]
			overlap = float(len(v))/self.max_queries
			if overlap <= 0.2:
				output['MINIMAL'].append((d, d_cats))
			elif 0.2 < overlap < 0.6:
				output['SOME'].append((d, d_cats))
			elif overlap >= 0.6:
				output['HIGH'].append((d, d_cats))
		degrees = ['HIGH', 'SOME', 'MINIMAL']
		print '\n'
		for deg in degrees:
			if output[deg]:
				print '%s OVERLAP: ' % deg
				for d, cats in sorted(output[deg]):
					if cats:
						print d + ': ' + ','.join(cats)
					else:
						print d
				print '\n'

	def render_graph(self, domains):
		g = Graph()
		for domain in domains.keys():
			if domain in self.cat_dict:
				categories = self.cat_dict[domain]
				stroke =  (0,0,0,0.5)
				if 'right' in categories:
					stroke = (255, 0, 0, 1)
				elif 'right_center' in categories:
					stroke = (255, 0, 0, .5)
				if 'left' in categories:
					stroke = (0,0,255, 1)
				elif 'left_center' in categories:
					stroke = (0,0,255, .5)
				if 'least_biased' in categories:
					stroke = (0,255,0, 1)

			fill = (128,128,0, 0.1)
			dub_cats = ['fake', 'questionable', 'clickbait', 'unreliable', 'conspiracy']
			score = len([c for c in categories if c in dub_cats])
			if score:
				fill = (0,0,0,float(score)/5)			
			g.add_node(domain, radius = len(domains[domain])*6, stroke = stroke, strokewidth = 6, fill = fill, font_size = 30)

		pairs = self.pairwise(domains.keys())
		for x, y in pairs:
			x_queries = set(domains[x])
			y_queries = set(domains[y])
			intersection = len(x_queries.intersection(y_queries))
			if intersection > 0:
				max_rad = max(len(domains[x]), len(domains[y]))+1000
				g.add_edge(x, y, length = max_rad, strokewidth = intersection)

		path = 'graph'
		g.export(path, encoding='utf-8', distance = 6, directed = False, width = 1400, height = 900)

def main():

	text = sys.argv[1]
	sc = SourceChecker(text)
	queries = sc.get_queries()
	domains = sc.get_urls(queries)
	sc.load_domains()
	sc.render_output(domains)
	sc.render_graph(domains)


if __name__ == "__main__":
    main()















