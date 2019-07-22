from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

import asyncio

class Scheduler(ABC):
    @abstractmethod
    async def schedule(self, url_queue: asyncio.Queue): ...

    @abstractmethod
    async def process(self, urls: List[str]): ...

class Fetcher(ABC):
    async def initialize(self): ...

    async def close(self): ...

    @abstractmethod
    async def fetch(self, url: str) -> str: ...

class Product(ABC):
    @abstractmethod
    def getFields() -> {}: ...

@dataclass
class ParseResult:
    links: List[str] = field(default_factory=list)
    product: Product = None

class Parser(ABC):
    @abstractmethod
    async def parse(self, url: str, html: str) -> ParseResult: ...

class Saver(ABC):
    @abstractmethod
    async def save(self, product) -> str: ...
