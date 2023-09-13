import asyncio
from zipfile import ZipFile
from typing import overload
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from pandas import DataFrame
import aiofiles


class PPTX:
    '''
    异步风格PPT操作类, 支持`async`/`await`
    '''

    def __init__(self, path):
        self._path = path
        self._zipfile = None

    async def __aenter__(self):
        async with aiofiles.open(self._path, "rb") as f:
            f
        self._zipfile = await asyncio.to_thread(ZipFile, self._path)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self._zipfile.close()

    async def open(self, file: str):
        '''打开文件二进制IO流'''
        if self._zipfile is None:
            raise ValueError
        fp = await asyncio.to_thread(self._zipfile.open, file)
        return fp

    async def read(self, file):
        '''读取二进制bytes'''
        fp = await self.open(file)
        with fp:
            return fp.read()

    async def slides(self):
        if self._zipfile is None:
            raise ValueError
        for file in self._zipfile.namelist():
            if file.startswith("ppt/slides/slide"):
                # read会迭代文件指针，可能影响速度
                # filebyte = await self.read(file)
                # relbyte = await self.read(f"ppt/slides/_rels/{file.split('/')[-1]}.rels")
                # slide = await Slide().fromByte(filebyte, relbyte)
                rel = f"ppt/slides/_rels/{file.split('/')[-1]}.rels"
                fp, frel = await asyncio.gather(self.open(file), self.open(rel))
                slide = await Slide().from_bufferedIO(fp, frel)
                yield slide

    async def get_tables(self) -> list[DataFrame]:
        tables = []
        async for slide in self.slides():
            tables += await slide.get_tables()
        return tables

    @overload
    async def get_image(self, xref: str):
        fb = await self.read(xref)
        return cv2.imdecode(np.fromstring(fb, dtype=np.uint8), 1)

    @overload
    async def get_image(self, index: int):
        return


class Slide:
    def __init__(self):
        self._bs = None
        self._rel = None
        self.namespace = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main"
        }

    async def from_bufferedIO(self, fp1, fp2):
        self._bs = ET.ElementTree(file=fp1)
        self._rel = ET.ElementTree(file=fp2)
        return self

    async def get_tables(self):
        res = []
        for table in self._bs.findall(".//a:graphicData", self.namespace):
            rows = table.findall(".//a:tr", self.namespace)
            if not rows or len(rows) < 2:
                continue
            heads = ["".join(col.itertext())
                     for col in rows[0].findall(".//a:tc", self.namespace)]
            if len(heads) > 10:
                continue
            data = [["".join(col.itertext()) for col in row.findall(
                ".//a:tc", self.namespace)] for row in rows[1:]]
            res.append(DataFrame(data, columns=heads))
        return res

    async def get_image_names(self):
        relations = self._rel.findall("Relationship")
        image_list = [
            r.get("Target").replace("..", "ppt")
            for r in relations
            if "media" in r.get("Target")
        ]
        return image_list


async def main():
    async with PPTX("1.pptx") as ppt:
        async for slide in ppt.slides():
            tables = await slide.get_tables()
            print(tables)

if __name__ == "__main__":
    asyncio.run(main())
