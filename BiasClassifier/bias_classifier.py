__author__ = "Masha Ivenskaya"

from argparse import ArgumentParser
import cPickle as pickle
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.pipeline import Pipeline
from collections import defaultdict
import sys 
from pattern.db  import Datasheet
from pattern.db  import pd
from random import shuffle
from time import strftime
from time import time
import logging
from sklearn.linear_model import LogisticRegression


class ItemSelector(BaseEstimator, TransformerMixin):
    def __init__(self, key):
        self.key = key

    def fit(self, x, y=None):
        return self

    def transform(self, data_dict):
        return data_dict[self.key]

class HeadlineBodyFeaturesExtractor(BaseEstimator, TransformerMixin):
    """Extracts the components of each input in the data: headline, body, and POS tags for each"""
    def fit(self, x, y=None):
        return self

    def transform(self, posts):
        features = np.recarray(shape=(len(posts),), dtype=[('headline', object), ('article_body', object)])
        for i, post in enumerate(posts): 
            headline, article = post[:2]
            features['headline'][i] = headline
            features['article_body'][i] = article
        return features

class BiasClassifier(object):
    
    def __init__(self, model=None, train=True, train_data=None,
                 dump=False, debug=False):
        """Intialize classifier, either from pre-trained model or from scratch"""
        self.debug = debug
        if model:
            try:
                self.pipeline_1 = self.load_model(model)
                self.pipeline_2 = self.load_model(model)
                self.model_name = model
            except Exception as e_load:
                logging.critical(str(e_load))
                self.classifier = None
        else:
            self.pipeline_1, self.pipeline_2 = self.train(train_data)

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
                pickle.dump(self.pipeline_1, f_pkl, pickle.HIGHEST_PROTOCOL)
                pickle.dump(self.pipeline_2, f_pkl, pickle.HIGHEST_PROTOCOL)
                self.model_name = model_file
            except pickle.PicklingError as e_pkl:
                print str(e_pkl) + ": continuing without dumping."

    def create_pipeline(self):
        pipeline = Pipeline([
    # Extract the subject & body
    ('HeadlineBodyFeatures', HeadlineBodyFeaturesExtractor()),

    # Use FeatureUnion to combine the features from subject and body
    ('union', FeatureUnion(
        transformer_list=[

            #Pipeline for pulling features from articles

            ('ngrams_title', Pipeline([
                 ('selector', ItemSelector(key='headline')),
                 ('vect', TfidfVectorizer(ngram_range=(1,3), token_pattern = r'\b\w+\b', max_df = 0.5)),
             ])),

             ('ngrams_text', Pipeline([
                 ('selector', ItemSelector(key='article_body')),
                 ('vect', TfidfVectorizer(ngram_range=(1,3), token_pattern = r'\b\w+\b', max_df = 0.5)),
             ])),
             ],
             )),

            ('logreg', LogisticRegression(penalty="l2", C=1.5, dual = True,  class_weight=None)),
            ])
        return pipeline

    def train(self, train_path):
    	""" Train classifier on features from headline and article text """
        if self.debug:
            tick = time()
            logging.info("Training new model with %s" % (train_path,))
            logging.info("Loading/shuffling training data...")
        
        train_data_1 = Datasheet.load(train_path)

        shuffle(train_data_1)
        train_texts_1 = zip(train_data_1.columns[0], train_data_1.columns[1])
        train_labels_1 = [0 if x == '0' else 1 for x in train_data_1.columns[-1]]      
        if self.debug:
        	logging.info('Fitting training data')
        pipeline_1 = self.create_pipeline()
        pipeline_1.fit(train_texts_1, train_labels_1)
        if self.debug:
            logging.info("Done in %0.2fs" % (time() - tick,))

        train_data_2 = Datasheet()
        for row in train_data_1.rows:
            if row[-1] != '0':
                train_data_2.append(row)
        train_texts_2 = zip(train_data_2.columns[0], train_data_2.columns[1])
        train_labels_2 = train_data_2.columns[-1]
        pipeline_2 = self.create_pipeline()
        pipeline_2.fit(train_texts_2, train_labels_2)
        return pipeline_1, pipeline_2
      

    def classify(self, inputs):
        """ Classifies inputs """
        responses = []
        prediction = self.pipeline_1.predict(inputs)
        for i, line in enumerate(inputs):
            if prediction[i] == 0:
                result = 0
            else:
                scores = self.pipeline_2.predict_proba([inputs[i]])[0]
                if scores[1]>scores[0]:
                    result = scores[1]
                elif scores[0]>scores[1]:
                    result = scores[0]*-1
                else:
                    result = 0
            line.append(result)
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


    clf = BiasClassifier(train_data=args.trainset,
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