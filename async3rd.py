import asyncio
from zipfile import ZipFile

import cv2
import numpy as np
from pandas import DataFrame
from bs4 import BeautifulSoup


class PPTX():
    def __init__(self, path):
        self._path = path
        self._zipfile = None

    async def __aenter__(self):
        self._zipfile = await asyncio.to_thread(ZipFile, self._path)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self._zipfile.close()

    async def open(self, file):
        if self._zipfile is None:
            raise ValueError
        fp = await asyncio.to_thread(self._zipfile.open, file)
        return fp

    async def read(self, file):
        fp = await self.open(file)
        with fp:
            return fp.read()

    async def slides(self):
        if self._zipfile is None:
            raise ValueError
        for file in self._zipfile.namelist():
            if file.startswith("ppt/slides/slide"):
                fp = await self.open(file)
                rel = await self.open(f"ppt/slides/_rels/{file.split('/')[-1]}.rels")
                with fp, rel:
                    slide = await Slide().fromIO(fp, rel)
                    yield slide

    async def get_tables(self) -> list[DataFrame]:
        tables = []
        async for slide in self.slides():
            tables += await slide.get_tables()
        return tables

    async def get_image(self, xref):
        fb = await self.read(xref)
        return cv2.imdecode(np.fromstring(fb, dtype=np.uint8), 1)


class Slide():
    def __init__(self):
        self._bs = None
        self._rel = None

    async def fromIO(self, fp, rel):
        tasks = [asyncio.to_thread(BeautifulSoup, i, features="xml")
                 for i in (fp, rel)]
        self._bs, self._rel = await asyncio.gather(*tasks)
        return self

    async def get_tables(self) -> list[DataFrame]:
        '''Get standard tables in slide'''
        res = []
        for table_tag in self._bs.find_all("a:graphicData"):
            rows = table_tag.find_all("a:tr")
            if not rows or len(rows) < 2:
                continue
            heads = [col.text for col in rows[0].find_all("a:tc")]
            data = [[col.text for col in row.find_all(
                "a:tc")] for row in rows[1:]]
            res.append(DataFrame(data, columns=heads))
        return res

    async def get_image_names(self):
        relations = self._rel.find_all("Relationship")
        image_list = [
            r["Target"].replace("..", "ppt")
            for r in relations
            if "media" in r["Target"]
        ]
        return image_list
