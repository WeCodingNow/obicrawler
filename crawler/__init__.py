from abc import ABC, abstractmethod
from .components import *
from .simple_fetcher import SimpleFetcherRPSC
from .simple_scheduler import SimpleScheduler

import asyncio

class Crawler(ABC):
    async def go(self, workers):
        components = self.getComponents()

        scheduler = components['Scheduler']
        fetcher = components['Fetcher']
        parser = components['Parser']
        saver = components['Saver']

        await fetcher.initialize()

        url_queue = asyncio.Queue()

        async def work():
            while True:
                url = await url_queue.get()
                html = await fetcher.fetch(url)
                parse_result = await parser.parse(url, html)
                await scheduler.process(parse_result.links)

                if parse_result.product:
                    await saver.save(parse_result.product)

                url_queue.task_done()

        tasks = [work() for _ in range(workers)]
        tasks.append(scheduler.schedule(url_queue))

        await asyncio.gather(*tasks)

        await fetcher.close()

    @abstractmethod
    def getComponents() -> {
        'Scheduler' : None,
        'Fetcher': None,
        'Parser' : None,
        'Saver' : None
    }: ...
