import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from elasticsearch import Elasticsearch

from crawler import Crawler, IndomainScheduler, SimpleFetcherRPSC, ParseResult, Parser, Saver, Product

from dataclasses import dataclass, field
from abc import ABC, abstractmethod

es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# TODO: сложная логика для: обновления товаров которые уже в БД
# TODO: для возобновления краулинга в случае остановки и т.д
class ObiScheduler(IndomainScheduler): ...
           
@dataclass
class ObiProduct(Product):
    id: int
    name: str
    image_link: str
    cost: str

    def getFields(self):
        return \
        {   'id':           self.id,
            'name':         self.name,
            'image_link':   self.image_link,
            'cost':         self.cost       }

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
            prod_id = int(link[link.rfind('/')+1:-1])
            name = bs.h1.get_text()
            image_link = bs.find(
                'img', title=name
            )['src']
            price = bs.find('strong', itemprop='price').get_text()

            pr.product = ObiProduct(prod_id, name, image_link, price)

        return pr

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

# супер-дегенеративный сохранятель
class ElasticSaver(Saver):
    async def save(self, product):
        res = es.index(index='obi', doc_type='product',id=product.id,body=product.getFields())
        print(res)


if __name__ == "__main__":
    url = 'https://www.obi.ru'
    c = ObiCrawler(saver=ElasticSaver(), rps=1, init_url=url)
    asyncio.run(c.go(1))
