import requests
import urllib
from bs4 import BeautifulSoup
from boilerpy3 import extractors

def extractor():
    extractor = extractors.ArticleExtractor()

    records = set()

    reddit_links = [
        "https://www.reddit.com/r/news/top/.rss?limit=100",
        "https://www.reddit.com/r/worldnews/top/.rss?limit=100",
        "https://www.reddit.com/r/news/.rss?limit=100",
        "https://www.reddit.com/r/worldnews/.rss?limit=100",
        "https://www.reddit.com/r/TechNewsToday/top/.rss?limit=100",
        "https://www.reddit.com/r/TechNewsToday/.rss?limit=100",
    ]

    for url in reddit_links:
        print('polling {}'.format(url))
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        request = urllib.request.Request(url,headers={'User-Agent': user_agent})
        response = urllib.request.urlopen(request)
        html = response.read()

        soup = BeautifulSoup(html,"xml")
        content = soup.find_all('content')

        for link in content:
            clean = str(link).replace('&amp;', '&')
            clean = clean.replace('&#32;', '')
            clean = clean.replace('&lt;', '<')
            clean = clean.replace('&gt;', '>')
            link_end = clean[:clean.find('">[link]')]
            link = link_end[link_end.find('<span><a href="')+15:]
            records.add(link)

    print('links extracted...')

    artcles = []
    errors = []
    for link in records:
        print('getting article {}'.format(link))
        try:
            doc = extractor.get_content_from_url(link)
            artcles.append({'title': 'test', 'body': doc, 'link': link})
        except Exception as e:
            errors.append(e)
    return artcles
    # [print(a) for a in artcles]
    # [print(err) for err in errors]