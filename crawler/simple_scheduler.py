from .components import Scheduler
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
