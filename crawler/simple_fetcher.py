from .components import Fetcher
import aiohttp
import asyncio
import time


class SimplestFetcher(Fetcher):
    async def fetch(self, url: str) -> str:
        import requests
        return requests.get(url).content

class SimpleFetcher(Fetcher):
    __slots__ = ['session']

    def __init__(self):
        self.session = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()

    async def fetch(self, url: str) -> str:
        print('fetching ', url)
        async with await self.session.get(url) as response:
            return await response.text()

# token bucket - декорируем aiohttp.ClientSession()
class RPSLimiter:
    MAX_TOKENS = 10

    def __init__(self, client, rate):
        self.client = client
        self.rate = rate
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()

    async def get(self, *args, **kwargs):
        print('waitin')
        await self.wait_for_token()
        return self.client.get(*args, **kwargs)

    async def wait_for_token(self):
        while self.tokens <= 1:
            self.add_new_tokens()
            await asyncio.sleep(1)

        self.tokens -= 1

    def add_new_tokens(self):
        now = time.monotonic()
        time_since_update = now - self.updated_at
        new_tokens = time_since_update * self.rate
        if self.tokens + new_tokens >= 1:
            self.tokens = min(self.tokens + new_tokens, self.MAX_TOKENS)
            self.updated_at = now

class RPSConstrained:
    def set_rps(self, rps: int):
        self.rps = rps

        return self

    async def initialize(self):
        await super().initialize()
        self.session = RPSLimiter(self.session, self.rps)

class SimpleFetcherRPSC(RPSConstrained, SimpleFetcher): ...

# нужно убрать точечку у .components чтобы заработал самотест
async def main():
    async def testFetcher(fetcher: Fetcher, *, url="https://google.com/"):
        await fetcher.initialize()

        async def request():
            html = await fetcher.fetch(url)
            print(html[0:50])

        for _ in range(10):
            await request()
        
        await fetcher.close()

    await testFetcher(SimpleFetcherRPSC().set_rps(1))


if __name__ == "__main__":
    asyncio.run(main())
