__author__ = "Masha Ivenskaya"

from argparse import ArgumentParser
import cPickle as pickle
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from collections import defaultdict
import string
import sys 
from pattern.db  import Datasheet
from pattern.db  import pd
import nltk
from random import shuffle
from pattern.en import sentiment
from pattern.en.wordlist import PROFANITY
from time import strftime
from time import time
import logging


class ItemSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, x, y=None):
        return self

    def transform(self, data_dict):
        return data_dict[self.key]

class Punct_Stats(BaseEstimator, TransformerMixin):
    """Extract punctuation features from each document"""

    def fit(self, x, y=None):
        return self

    def transform(self, text_fields):
        punct_stats = []
        punctuations = list(string.punctuation)
        additional_punc = ['``', '--', '\'\'']
        punctuations.extend(additional_punc)
        for field in text_fields:
            puncts = defaultdict(int)
            for ch in field:
                if ch in punctuations:
                    puncts[ch]+=1
            punct_stats.append(puncts)
        return punct_stats


class Text_Stats(BaseEstimator, TransformerMixin):
    """Extract text statistics from each document"""

    def fit(self, x, y=None):
        return self

    def transform(self, text_fields):
        stats = []
        punctuation = string.punctuation
        abvs = ['CNN', 'FBI', 'ABC', 'MSNBC', 'GOP', 'U.S.', 'US', 'ISIS', 'DNC', 'TV', 'CIA', 'I', 'AP', 'PM', 'AM', 'EU', 'USA', 'UK', 'UN', 'CEO', 'NASA', 'LGBT', 'LGBTQ', 'NAFTA', 'ACLU']
        for field in text_fields:
            field_stats = {}
            tok_text = nltk.word_tokenize(field)
            try:
                num_upper = float(len([w for w in tok_text if w.isupper() and w not in abvs]))/len(tok_text)
            except:
                num_upper = 0
            try:
                num_punct = float(len([ch for ch in field if ch in punctuation]))/len(field)
            except:
                num_punct = 0   
            try:
                sent_lengths = [len(nltk.word_tokenize(s)) for s in nltk.sent_tokenize(field)]
                av_sent_len = float(sum(sent_lengths))/len(sent_lengths)
            except:
                av_sent_len = 0
            try:
                num_prof = float(len([w for w in tok_text if w.lower() in PROFANITY]))/len(tok_text)
            except:
                num_prof = 0

            polarity, subjectivity = sentiment(field)
            field_stats['all_caps'] = num_upper
            field_stats['sent_len'] = av_sent_len
            field_stats['polarity'] = polarity
            field_stats['subjectivity'] = subjectivity
            field_stats['profanity'] = num_prof
            stats.append(field_stats)
        return stats


class HeadlineBodyFeaturesExtractor(BaseEstimator, TransformerMixin):
    """Extracts the components of each input in the data: headline, body, and POS tags for each"""
    def fit(self, x, y=None):
        return self

    def transform(self, posts):
    	punctuation = string.punctuation
        features = np.recarray(shape=(len(posts),), dtype=[('headline', object), ('article_body', object), ('headline_pos', object), ('body_pos', object)])
        for i, post in enumerate(posts): 
            headline, article = post[:2]
            features['headline'][i] = headline
            features['article_body'][i] = article

            tok_headline = nltk.word_tokenize(headline)
            features['headline_pos'][i] = (' ').join([x[1] for x in nltk.pos_tag(tok_headline)])

            tok_article = nltk.word_tokenize(article)
            features['body_pos'][i] = (' ').join([x[1] for x in nltk.pos_tag(tok_article)])

        return features

class SensationalismClassifier(object):
    
    def __init__(self, model=None, train=True, train_data=None,
                 dump=False, debug=False):
        """Intialize classifier, either from pre-trained model or from scratch"""
        self.debug = debug
        if model:
            try:
                self.pipeline = self.load_model(model)
                self.model_name = model
            except Exception as e_load:
                logging.critical(str(e_load))
                self.classifier = None
        else:
            self.pipeline = self.train(train_data)
            if dump:
                self.dump_model()

    def load_model(self, model_file=None):
    	""" Load model from pre-trained pickle"""
        if self.debug:
            logging.info("Loading model %s" % model_file)
        try:
            with open(model_file, "rb") as pkl:
                pipeline = pickle.load(pkl)
        except (IOError, pickle.UnpicklingError) as e:
            logging.critical(str(e))
            raise e
        return pipeline

    def dump_model(self, model_file="model_%s.pkl" % strftime("%Y%m%d_%H%M")):
        """ Pickle trained model """
        if self.debug:
            logging.info("Dumping model to %s" % model_file)
        with open(model_file, "wb") as f_pkl:
            try:
                pickle.dump(self.pipeline, f_pkl, pickle.HIGHEST_PROTOCOL)
                self.model_name = model_file
            except pickle.PicklingError as e_pkl:
                print str(e_pkl) + ": continuing without dumping."


    def train(self, train_path):
    	""" Train classifier on features from headline and article text """
        if self.debug:
            tick = time()
            logging.info("Training new model with %s" % (train_path,))
            logging.info("Loading/shuffling training data...")
        
        train_data = Datasheet.load(train_path)
        shuffle(train_data)
        train_texts = zip(train_data.columns[0], train_data.columns[1])
        train_labels = train_data.columns[-1]
        pipeline = Pipeline([
    # Extract the subject & body
    ('HeadlineBodyFeatures', HeadlineBodyFeaturesExtractor()),

    # Use FeatureUnion to combine the features from subject and body
    ('union', FeatureUnion(
        transformer_list=[

            #Pipeline for pulling features from articles

            ('punct_stats_headline', Pipeline([
                ('selector', ItemSelector(key='headline')),
                ('stats', Punct_Stats()),  # returns a list of dicts
                ('vect', DictVectorizer()),  # list of dicts -> feature matrix
            ])),

            ('punct_stats_body', Pipeline([
                ('selector', ItemSelector(key='article_body')),
                ('stats', Punct_Stats()),  # returns a list of dicts
                ('vect', DictVectorizer()),  # list of dicts -> feature matrix
            ])),

             ('pos_ngrams_headline', Pipeline([
                 ('selector', ItemSelector(key='headline_pos')),
                 ('vect', CountVectorizer(ngram_range=(1,2), token_pattern = r'\b\w+\b', max_df = 0.5)),
             ])),

             ('pos_ngrams_body', Pipeline([
                 ('selector', ItemSelector(key='body_pos')),
                 ('vect', CountVectorizer(ngram_range=(1,2), token_pattern = r'\b\w+\b', max_df = 0.5)),
             ])),

            ('text_stats_headline', Pipeline([
                ('selector', ItemSelector(key='headline')),
                ('stats', Text_Stats()),  # returns a list of dicts
                ('vect', DictVectorizer()),  # list of dicts -> feature matrix
            ])),

            ('text_stats_body', Pipeline([
                ('selector', ItemSelector(key='article_body')),
                ('stats', Text_Stats()),  # returns a list of dicts
                ('vect', DictVectorizer()),  # list of dicts -> feature matrix
            ])),
        ],
    )),

    # Use an SVC classifier on the combined features
    ('svc', SVC(C=1.0)),
])

        if self.debug:
        	logging.info('Fitting training data')
        pipeline.fit(train_texts, train_labels)
        if self.debug:
            logging.info("Done in %0.2fs" % (time() - tick,))
        return pipeline
      

    def classify(self, inputs):
        """ Classifies inputs """
        responses = []
        results = self.pipeline.predict(inputs)
        for i, line in enumerate(inputs):
            line.append(results[i])
            responses.append(line)
        return responses

def main():
    logging.basicConfig(level=logging.INFO)

    argparser = ArgumentParser(description=__doc__)
    argparser.add_argument("-t", "--trainset", action="store",
                           default=None,
                           help=("Path to training data "
                                 "[default: %(default)s]"))
    argparser.add_argument("-m", "--model", action="store",
                           help="Path to model")
    argparser.add_argument("-d", "--dump", action="store_true",
                           help="Pickle trained model? [default: False]")
    argparser.add_argument("-v", "--verbose", action="store_true",
                           default=False,
                           help="Verbose [default: quiet]")
    argparser.add_argument("-c", "--classify", action="store",
                           default=None,
                           help=("Path to data to classify "
                                 "[default: %(default)s]"))
    argparser.add_argument("-s", "--save", action="store",
                           default='output.csv',
                           help=("Path to output file"
                                 "[default = output.csv]"))
    args = argparser.parse_args()


    clf = SensationalismClassifier(train_data=args.trainset,
                                    model=args.model,
                                    dump=args.dump,
                                    debug=args.verbose)

    if args.classify:
    	OUTPUT_PATH = args.save

        if clf.debug:
            tick = time()
        to_classify = Datasheet.load(args.classify)
        classified_data = clf.classify(to_classify)
        output = Datasheet(classified_data)
        output.save(pd(OUTPUT_PATH))

        if clf.debug:
            sys.stderr.write("\nProcessed %d items in %0.2fs" %
                            (len(classified_data), time() - tick))

if __name__ == "__main__":
    main()