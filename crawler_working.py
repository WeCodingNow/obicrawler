import aiohttp
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from urllib.parse import urlparse

from bs4 import BeautifulSoup

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

@dataclass
class Page:
    productName: str
    productDescription: str
    productImage: str

@dataclass
class ParseResult(ABC):
    links: List[str] = field(default_factory=list)
    isProduct: bool = False

class Parser(ABC):
    @abstractmethod
    def parse(self, html: str) -> ParseResult: ...

@dataclass
class ObiParseResult(ParseResult):
    productName: str = ""
    productDescription: str = ""
    productImageLink: str = ""

    def makePage(self):
        return Page(
            self.productName,
            self.productDescription,
            self.productImageLink
        )

class ObiParser(Parser):
    def parse(self, link: str, html: str):
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
            print(pr.productName, pr.productImageLink)

        return pr


class Crawler:

    def __init__(self, url, *, workers=1, rps=10, parser):
        self.rootUrl = url
        self.domainName = urlparse(url).netloc
        self.unvisitedLinks = [url]
        self.storage = {
            'visitedLinks': [],
            'productPages': []
        }

        # customization points
        self.workers = workers
        self.queue = asyncio.Queue(rps)
        self.rps = rps
        self.parser = parser

        print(f'crawling {self.domainName}...')


    async def visit(self, link, session):
        print(f'visiting {link}...')
        self.storage['visitedLinks'].append(link)

        html = await fetch(session, link)
        parseResult = self.parser.parse(link, html)

        unvisitedUrls = filter(
            lambda url: \
                url and \
                url not in self.storage['visitedLinks'] \
                and self.domainName in url,
            parseResult.links
        )

        self.unvisitedLinks += unvisitedUrls

        if parseResult.isProduct:
            self.storage['productPages'].append(parseResult.makePage())


    async def go(self):
        async with aiohttp.ClientSession() as session:

            async def scheduleRequests():
                while True:
                    for request in range(self.rps):
                        try:
                            await self.queue.put(self.unvisitedLinks.pop())
                        except:
                            break

                    await asyncio.sleep(1)

            async def do(worker):
                while True:
                    link = await self.queue.get()
                    print(f'worker {worker} workin\' on: ', end='')
                    await self.visit(link, session)

            await asyncio.gather(
                scheduleRequests(),
                *[do(i) for i in range(self.workers)]
            )


async def main():
    url = 'https://www.obi.ru'

    c = Crawler(url, parser=ObiParser(), workers=5, rps=10)
    await c.go()

asyncio.run(main())
