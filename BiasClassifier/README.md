The Bias Classifier directory on Github contains the trained model, as well as Python code to train a model and to classify new data, the data used for training, and a sample of test data (a held-out set) with true labels and the classifier scores.  In the training data, label ‘0’ corresponds to the ‘least-biased’ class, ‘1’ corresponds to ‘left’, and ‘2’ corresponds to ‘right’. 
 
This classifier takes as input a 2-column CSV file, where the first column corresponds to the headlines and second one corresponds to the article texts. 
 
Usage for the Python code:
 
	python bias_classifier.py -args

	The arguments are:
	-t, --trainset: Path to training data (if you are training a model)
	-m, --model: Path to model (if you are using a pre-trained model)
	-d, --dump: Dump trained model? Default is False
	-v, --verbose: Default is non-verbose
	-c, --classify: Path to new inputs to classify
	-s, --save: Path to the output file (default is 'output.csv')

Output:
 
	The output is a number between -1 and 1, where -1 is most left-biased, 1 is most right-biased, and 0 is least-biased.
 
 
Data:
 
	The articles come from the crawled data - a hand-picked subset of sites that were labeled as "right", "right-center", "left", "left-center", and "least-biased" by mediabiasfactcheck.com.   I used one subset of sources for the training data and a different subset of sources for the testing data in order to avoid overfitting.   I also trained a separate model on all of the sources I had available - since it is trained on more data, it may perform better. This model is also available in the Github directory under the name “trained_model_all_sources.pkl”
	 
	It is worth noting that articles from  'right-center' and 'left-center' sources often exhibit only a subtle bias, if any at all.  This is because the bias of these sources is often not evident on a per-article basis, but only on a per-source basis.  It may exhibit itself, for example, through story selection rather than through loaded language.  For this reason I did not include articles from 'right-center' and 'left-center' sources in the training data, but I did use them for evaluation. 
	 
Architecture:
 
	The classifier has a two-tiered architecture, where first the unbiased articles are filtered out, and then a second model distinguishes between right and left bias.  Both models are Logistic Regressions based on lexical n-gram features, implemented through scikit-learn.
	 
Features:
 
	Both models rely on bag-of-word n-gram features (unigrams, bigrams, trigrams).
 
Results:
 
	The output is a number between -1 and 1, where -1 is most left-biased, 1 is most right-biased, and 0 is least-biased. For evaluation purposes, scores below 0 are considered “left”, above 0 are considered “right”, and 0 is considered “least-biased”. 
	 
	As previously mentioned, along with the 3 classes that are present in the training data, there are two addition in-between classes that I used for evaluation only.  
	 
	In order to be counted as correct for recall, right-center can be predicted as either 'right' or 'least-biased', and left-center can be predicted as 'left' or 'least-biased'.  In addition, when calculating the precision of the 'least-biased' class,  'least-biased', 'right-center' and 'left-center' true classes all count as correct. 
 
 
Class			Precision	Recall
Right			45% 		82%
Left 			70% 		71%
Right-center 	N/A 		70%
Left-center 	N/A 		60%
Least-biased 	96% 		33%

 
Note:
 
	Unlike the Sensationalism classifier, this classifier relies on lexical features, which may be specific to the current political climate etc.  This means that the training data might "expire" and as a result the accuracy could decrease.  
