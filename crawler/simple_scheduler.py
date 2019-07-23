from .components import Scheduler
from urllib.parse import urlparse
import asyncio

class SimpleScheduler(Scheduler):
    def __init__(self, *initial_url):
        self.next_urls_queue = asyncio.Queue()

        for url in initial_url:
            self.next_urls_queue.put_nowait(url)

    def attach_source(source):
        self.source = source

    async def schedule(self, url_queue: asyncio.Queue):
        while True:
            next_url = await self.next_urls_queue.get()
            await url_queue.put(next_url)
            self.next_urls_queue.task_done()

    async def process(self, urls):
        for url in urls:
            self.next_urls_queue.put_nowait(url)

class IndomainScheduler(SimpleScheduler):
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

        for url in indomain_urls:
            await self.next_urls_queue.put(url)

        self.visited_urls += urls