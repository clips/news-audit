Usage:

	python source_checker.py "text snippet" (language)

What it does:

	Input: Snippet of text (as a command line argument)

	Command line output: Domains where parts of the snippet appear, by amount of overlap. If the domain is in our database (i.e. the compiled file of domains from MBFC, Politifact, and OpenSources), the category or categories assigned by these is also returned.

	Graph output:

		The circles in the graph correspond to returned domains.
		Circle size corresponds to amount of overlap between the input snippet and the domain.
		Circle border color corresponds to bias: blue = left, red = right, green = neutral, grey = unknown.
		Circle fill corresponds to unreliability: black circles are classified by one of the lists as either fake, unreliable, clickbait, questionable, or conspiracy. The blacker the circle - the more unreliable it is.
		Edges that connect circles correspond to overlap of statements - the thicker the edge, the bigger the overlap.
		The graph output needs quite a bit of work - I am still trying to figure out how to best present the information, how to tune the parameters, and I am very open to suggestions from someone more experienced with visualization.

Example:

	Input:

		"It doesn’t get much more liberal than Michael Moore. The guy was speaking at women’s marches for goodness sake, and he’s so liberal that the women let him. He seems to have built his entire career on career solely on criticizing people (especially conservatives) and for some reason, people love him for it. Unlike most liberals though, Moore isn’t discriminatory about who he gets fed up with, and this time, it’s his own party. Apparently, the Michigan-born Democrat was ready for a win in the much-anticipated Georga special election and he’s a little ticked off that he didn’t get it, which caused this ultra liberal to say what the rest of us have been thinking about the Democratic party. Liberal activist Michael Moore lashed out at national Democrats on Wednesday after the party fell short in a special House runoff election in Georgia despite spending tens of millions of dollars on a race that was viewed as a referendum on President Trump. Moore ripped the Democratic National Committee and its House campaign arm for having “no message, no plan, no leaders.” Democratic leaders “hate the resistance,” Moore said, underscoring the lingering tension between the party’s grassroots base and the establishment in Washington. The district is reliably red, but Democrats, eager to make a statement about the strength of their grassroots fury, went all-in to turn the district blue, casting the election as a referendum on Trump and pouring millions of dollars into the race. Liberals have turned out for huge anti-Trump protests across the country and have made life miserable for GOP lawmakers at town halls in their home districts, but Republicans nonetheless won all four special elections this year. I guess when it comes to politics loudest doesn’t always mean most forceful. Yes, the Democrats have been rallying"

	Output:

		HIGH OVERLAP:

		yesimright.com: questionable, fake, bias

		SOME OVERLAP:

		nation45.com
		polination.wordpress.com
		redstatewatcher.com: right, bias, clickbait
		theblacksphere.net: right
		thehill.com: left_center

		MINIMAL OVERLAP:

		bwcentral.org
		commentators.com
		hotair.com: right
		longroom.com
		nation.foxnews.com
		patrick.net
		thefederalistpapers.org: questionable
		townhall.com: right
		youngcons.com: right


Architecture:

	The text snippet is broken down into n-grams using the Pattern n-gram module. N-grams that consist primarily of stop-words or named entities are discarded. A sample of the remaining n-grams is reconstructed into the original strings and run through the Google API as an exact phrase (in quotation marks) . Currently, I am using 15-token n-grams (continuous, i.e. across sentence boundaries), and I take 10 evenly-spaced n-grams regardless of the size of the text snippet - so if there are a total of 30 n-grams, every 3rd n-gram is selected, if there 50 every 5th, etc. The returned domains are then rated by the amount of queries that returned that domain (more than 6 out of 10 = "high overlap", 3 to 6 = "some overlap", less than 3 = "minimal overlap"), and matched against our database. The graph is rendered using the Pattern Graph module.


Multi-lingual feature:

	This tool has the ability to handle non-English text.  I modified the architecture so that the language can be specified as an optional second argument. If NLTK provides stop-words for the language, the n-grams get filtered by percentage of stop-words, but not by percentage of named entities, since NLTK does not provide named entity recognition for non-English. If it's a language for which NLTK does not provide stop-words, n-grams do not get filtered at all. This may result in slightly lower accuracies for those languages, but since I only had English data, I had no way of evaluating the accuracy. One way of improving this tool for non-English data would be to incorporate named entity and stop-word filtering for those langauges where the tools were not available. 

Dependencies:

	Mostly uses Pattern. Depends on NLTK for stop-word and entity filtering (this is somewhat optional).

Evaluation:

	For evaluation, I used 300 article snippets from the data that I have crawled. The snippets are from varied sources (right-biased, left-biased, least-biased, unreliable, etc) and of variable length (100-500 word counts). Since I know where I crawled a given article, there's a true label for each snippet. If the true label appears in the list of domains returned by the Source Checker, the output is considered correct. By this metric, the current accuracy is around 74%. Generally, the longer the snippet the better the accuracy (88% on 500-word snippets). The reason for the misses seems to stem from the Google API: I have noticed that for many queries, the API output doesn't match the output I get when I run the same exact query through regular Google web search: there are usually much fewer results through the API. In every case that I tried to debug, this was the reason for the miss. I am still in the process of figuring out why this happens and if there's a fix.

	However - there seems to be quite a bit of statement overlap between the categories of sources - especially between unreliable/fake sources (which is something that might be worth exploring in more detail). This means that even if we don't catch the exact source that published a given piece of text, the output will still provide a reasonably good idea of the types of sources that publish it (or parts of it).

