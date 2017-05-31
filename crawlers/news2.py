# Crawls sensationalist articles from dailystar.co.uk,
# each time the script runs.

from pattern.web import Newsfeed
from pattern.web import URL
from pattern.web import DOM
from pattern.web import plaintext

from pattern.db import Datasheet
from pattern.db import pd


feeds = {
     'boorish': 'http://feeds.feedburner.com/daily-star-Real-Life',
    'dramatic': 'http://feeds.feedburner.com/daily-star-Latest-News',
       'geeky': 'http://feeds.feedburner.com/daily-star-Tech',
     'dubious': 'http://feeds.feedburner.com/daily-star-Weird-News',
      'vulgar': 'http://feeds.feedburner.com/daily-star-Love-Sex',
}

PATH = pd('..', 'data', 'news2.csv') # pd = parent directory of this script

try:
    csv = Datasheet.load(PATH)
    seen = set(csv.columns[0])
except:
    csv = Datasheet()
    seen = set()

for genre, url in feeds.items():
    for r in Newsfeed().search(url, cached=False):
        if r.url not in seen:
            print r.title
            print
            try:
                src = URL(r.url).download(cached=True)
                dom = DOM(src)
                txt = []

                # Daily Star has untidy HTML markup.
                # Collect the article <p> by <p>.
                for p in dom('.story-content p'):
                    if p.parent.tag == 'blockquote':
                        continue
                    s = plaintext(p)
                    s = s.strip()
                    if s != s.upper(): # Exclude references ("GETTY", "YOUTUBE").
                        txt.append(s)

                seen.add(r.url)
                csv.append((
                    r.url, 
                    r.title, 
                    '\n\n'.join(txt), 
                    genre
                ))
            except:
                pass
    csv.save(PATH)