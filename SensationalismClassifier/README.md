This model currently achieves an F-score of 92% (obtained through 5-fold cross-validation). It is trained on 8000 sensational and 8000 objective headlines and articles.

It takes as input a 2-column CSV file, where the first column corresponds to the headlines and second one corresponds to the article texts. The output file contains a third column with the label - 1 if the input is categorized as sensationalist, 0 if not.

The classifier is a non-linear SVM, and it uses the following features:

	POS tags (unigrams and bigrams)

	Punctuation counts

	Average sentence length

	Number of all-cap tokens (excluding common abbreviations, and normalized by length of text)

	Number of words that overlap with the Pattern Profanity word list (normalized by length of text)

	Polarity and Subjectivity scores (obtained through the Pattern Sentiment module)

This directory contains the trained model, as well as Python code to train a model and to classify new data, the data used for training, and a sample of test data (a held-out set) with TRUE labels.

Usage for the Python code

	python SensationalClassifier.py -args

	The arguments are:

	-t, --trainset: Path to training data (if you are training a model)

	-m, --model: Path to model (if you are using a pre-trained model)

	-d, --dump: Dump trained model? Default is False

	-v, --verbose: Default is non-verbose

	-c, --classify: Path to new inputs to classify

	-s, --save: Path to the output file (default is 'output.csv')

Experiments and Results

	Below is the classification report for the final model:

		precision	recall	f-score
		objective	0.91	0.93	0.92
		sensationalist	0.92	0.91	0.92

	Below are f-scores for models trained on subsets of features (text statistics refers to the combination of sentence length, all-caps, profanity, polarity, and subjectivity features):

		Features	F-score
		Text Stats	71
		Punctuation	85
		POS unigrams	79
		POS bigrams	86
		Text Stats + Punctuation	86
		Text Stats + POS Bigrams	88
		Punctuation + POS Bigrams	91
		Text Stats + Punctuation + POS Bigrams	92

This model is trained on features from both the headlines and the articles. Training the same model ONLY on headlines or ONLY on articles results in lower f-scores (82% and 89% respectively).

Dependenices

	- Scikit-learn for modeling

	- NLTK for POS-tagging

	- Pattern for Polarity, Subjectivity, and Profanity features

