import asyncio
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from typing import overload

import cv2
import numpy as np
from pandas import DataFrame
from bs4 import BeautifulSoup

class PPTX():
    '''
    异步风格PPT操作类, 支持`async`/`await`
    '''

    def __init__(self, path):
        self._path = path
        self._zipfile = None

    async def __aenter__(self):
        self._zipfile = await asyncio.to_thread(ZipFile, self._path)
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        self._zipfile.close()

    async def read(self, file):
        if self._zipfile is None:
            raise ValueError
        filebyte = await asyncio.to_thread(self._zipfile.read, file)
        return filebyte

    async def slides(self):
        if self._zipfile is None:
            raise ValueError
        for file in self._zipfile.namelist():
            if file.startswith("ppt/slides/slide"):
                rel = f"ppt/slides/_rels/{file.split('/')[-1]}.rels"
                filebyte, relbyte = await asyncio.gather(self.read(file), self.read(rel))
                slide = await Slide().fromByte(filebyte, relbyte)
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
        bs = BeautifulSoup(slide, features="xml")
        title = bs.find("p:ph", type="title")
        if title and title.parent.parent.parent.text==pic:
            # 提取图片
            rel = f"ppt/slides/_rels/{s.split('/')[-1]}.rels"
            with ppt.open(rel) as slide_rel:
                rel_bs = BeautifulSoup(slide_rel, features="xml")
                relationships = rel_bs.find_all("Relationship")
                for re in relationships:
                    if "media" in re["Target"]:
                        img = re["Target"].replace("..", "ppt")
                ppt.extract(img, f"{sec.pid}/SEC")
                img = f"{sec.pid}/SEC/{img}"
        return


class Slide():
    '''
    异步风格Slide操作类, 支持`async`/`await`
    '''

    def __init__(self):
        self._bs = None
        self._rel = None

    async def fromByte(self, file, rel):
        tasks = [asyncio.to_thread(BeautifulSoup, i, features="xml")
                 for i in (file, rel)]
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
        # 这样获取的图片可能存在显示与原图片发生变换
        relations = self._rel.find_all("Relationship")
        image_list = [
            r["Target"].replace("..", "ppt")
            for r in relations
            if "media" in r["Target"]
        ]
        return image_list
    
class XmlSlide():
    def __init__(self):
        self._bs = None
        self._rel = None
    
    def from_byte(self, file, rel):
        
        self._bs = ET.parse()
        self._rel = ET.parse()
