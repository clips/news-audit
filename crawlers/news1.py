# Each time you run this script (which requires Pattern),
# it collects articles from known sources and their bias,
# and appends to a CSV-file (/data/news1.csv)

from pattern.db  import Datasheet
from pattern.db  import pd
from pattern.web import Newsfeed
from pattern.web import URL
from pattern.web import DOM
from pattern.web import plaintext

# To estimate the level of bias:
# https://mediabiasfactcheck.com
# http://www.fakenewschecker.com

sources = { 

    (4, 'right', 'fake', 'Departed'                  ) : 'http://americansmaga.info/feed/',
    (4, 'right', 'fake', 'Hang The Bankers'          ) : 'http://www.hangthebankers.com/feed/',
    (4, 'right', 'fake', 'News Busters'              ) : 'http://www.newsbusters.org/blog/feed',
    (4, 'right', 'fake', 'Truth Revolt'              ) : 'http://www.truthrevolt.org/rss.xml',
    (4, 'right', 'fake', 'Young Conservatives'       ) : 'http://www.youngcons.com/feed/',
    (4, 'right', 'fake', 'American Free Press'       ) : 'http://americanfreepress.net/feed/',
    (4, 'right', 'fake', 'Liberty Writers News'      ) : 'https://libertywritersnews.com/feed/rss',
    (4, 'right', 'fake', 'Prntly'                    ) : 'http://prntly.com/feed/',
    (3, 'right', 'fake', 'The Federalist Papers'     ) : 'http://thefederalistpapers.org/feed',
    (3, 'right', 'fake', 'BlabberBuzz'               ) : 'http://www.blabber.buzz/politics/conservative?format=feed',
    (3, 'right', 'fake', 'World Net Daily'           ) : 'http://mobile.wnd.com/category/front-page/us/feed/',
    (3, 'right', 'fake', 'Infowars'                  ) : 'http://www.infowars.com/feed/custom_feed_rss',
    (3, 'right', 'fake', 'Freedom Daily'             ) : 'http://freedomdaily.com/feed',
    (2, 'right', 'real', 'Heat Street'               ) : 'https://heatst.com/feed/',
    (2, 'right', 'real', 'Breitbart'                 ) : 'http://feeds.feedburner.com/breitbart',
    (1, 'right', 'real', 'Fox News'                  ) : 'http://feeds.foxnews.com/foxnews/latest',

    (3, 'left' , 'fake', 'Realtime Politics'         ) : 'http://realtimepolitics.com/feed/rss',
    (3, 'left' , 'fake', 'Counter Current News'      ) : 'http://countercurrentnews.com/feed/',
    (2, 'left' , 'real', 'Upworthy'                  ) : 'http://feeds.feedburner.com/upworthy',
    (2, 'left' , 'real', 'Mother Jones'              ) : 'http://www.motherjones.com/rss/blogs_and_articles/feed',
    (2, 'left' , 'real', 'Slate'                     ) : 'http://www.slate.com/all.fulltext.all.rss',
    (2, 'left' , 'real', 'The Hill'                  ) : 'http://thehill.com/rss/syndicator/19110',
    (2, 'left' , 'real', 'Huffington Post'           ) : 'http://www.huffingtonpost.com/feeds/index.xml',
    (1, 'left' , 'real', 'New York Times'            ) : 'http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    (1, 'left' , 'real', 'Washington Post'           ) : 'http://feeds.washingtonpost.com/rss/rss_blogpost',

    (0, ''     , 'real', 'Reuters'                   ) : 'http://feeds.reuters.com/reuters/topNews',
    (0, ''     , 'real', 'USA Today'                 ) : 'http://rssfeeds.usatoday.com/usatoday-NewsTopStories',
    (0, ''     , 'real', 'Financial Times'           ) : 'http://www.ft.com/rss/world',
    (0, ''     , 'real', 'Associated Press'          ) : 'http://hosted2.ap.org/atom/APDEFAULT/3d281c11a96b4ad082fe88aa0db04305',
    (0, ''     , 'real', 'The Diplomat'              ) : 'http://thediplomat.com/feed/',
    (0, ''     , 'real', 'United Press International') : 'http://rss.upi.com/news/news.rss',
    
    (0, ''     , 'joke', 'The Onion'                 ) : 'http://www.theonion.com/feeds/rss',
    (4, 'right', 'joke', 'National Report'           ) : 'http://feeds.feedburner.com/NationalReport',

}

PATH = pd('..', 'data', 'news1.csv')

try:
    csv = Datasheet.load(PATH)
    seen = set(csv.columns[-2]) # use url as id
except:
    csv = Datasheet()
    seen = set()

for (level, bias, label, name), url in sources.items():
    try:
        f = Newsfeed()
        f = f.search(url, cached=False)
    except:
        continue

    for r in f:

        # 1) Download source & parse the HTML tree:
        try:
            src = URL(r.url).download(cached=True)
            dom = DOM(src)
        except Exception as e:
            continue

        # 2) Find article text w/ CSS selectors:
        for selector in (
      "article[class*='node-article']",            # The Hill
         "span[itemprop='articleBody']",
          "div[itemprop='articleBody']",
          "div[id='rcs-articleContent'] .column1", # Reuters
          "div[class='story-body']",
          "div[class='article-body']",
          "div[class='article-content']",
          "div[class^='tg-article-page']",
          "div[class^='newsArticle']",
          "div[class^='article-']",
          "div[class^='article_']",
          "div[class*='article']",
          "div[id*='storyBody']",                  # Associated Press
          "article",
          ".story"):
            e = dom(selector)
            if e:
                e = e[0]
                break

        # 3) Remove ads, social links, ...
        try:
            e("div[id='rightcolumn']")[0]._p.extract()
            e("div[class='section-blog-right']")[0]._p.extract()
            e("div[class='blog-sidebar-links']")[0]._p.extract()
            e("div[role='complementary']")[0]._p.extract()
        except:
            pass

        # 4) Remove HTML tags:
        try:
            s = plaintext(e)
            s = s.strip()
        except:
            continue

        #if not s:
        #    print r.url
        #    print
        #    continue

        # 5) Save to CSV:
        if r.url not in seen:
            seen.add(r.url)
            csv.append((
                name, 
                label, 
                bias, 
                str(level), 
                r.title, 
                s, 
                r.url, 
                r.date
            ))
            print name, r.title
            print

    csv.save(pd(PATH))

# To read the dataset:
# for name, label, bias, level, title, article, url, date in Datasheet.load(PATH):
#     level = int(level)