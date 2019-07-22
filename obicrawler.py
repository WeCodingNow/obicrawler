import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from crawler import Crawler, SimpleScheduler, SimpleFetcherRPSC, ParseResult, Parser, Saver

class ObiScheduler(SimpleScheduler):
    def __init__(self, root_url):
        super().__init__(root_url)
        self.root_url = root_url
        self.domain_name = urlparse(root_url).netloc
        self.visited_urls = []

    async def process(self, urls):

        urls = set(urls)

        indomain_urls = list(filter(
           lambda url: url and \
               url not in self.visited_urls \
               and self.domain_name in url,
               urls
        ))

        self.visited_urls += urls

        for url in indomain_urls:
            self.next_urls_queue.put_nowait(url)
           

class ObiProduct:
    ...

class ObiParseResult(ParseResult):
    ...

class ObiParser(Parser):
    async def parse(self, link: str, html: str):
        bs = BeautifulSoup(html, 'html.parser')

        pr = ObiParseResult()

        for a_tag in bs.find_all('a'):
            url = a_tag.get('href')
            pr.links.append(url)

        if '/p/' in link:
            pr.isProduct = True
            pr.productName = bs.h1.get_text()
            pr.productImageLink = bs.find(
                'img', title=pr.productName
            )['src']

        return pr

class ElasticSaver(Saver):
    async def save(self, product):
        print(product)

class ObiCrawler(Crawler):
    def __init__(self, *, saver: Saver, rps=1, init_url=None):
        self.saver = saver
        self.rps = rps
        self.init_url = init_url

    def getComponents(self):
        return {
           'Scheduler' : ObiScheduler(self.init_url),
           'Fetcher' : SimpleFetcherRPSC().set_rps(self.rps),
           'Parser' : ObiParser(),
           'Saver' : self.saver
        }
        

if __name__ == "__main__":
    url = 'https://www.obi.ru'
    c = ObiCrawler(saver=ElasticSaver(), rps=5, init_url=url)
    asyncio.run(c.go(10))