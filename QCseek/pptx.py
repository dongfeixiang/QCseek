import asyncio
from zipfile import ZipFile
import xml.etree.ElementTree as ET
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
    async def open(self, file):
        if self._zipfile is None:
            raise ValueError
        fp = await asyncio.to_thread(self._zipfile.open, file)
        return fp

    async def get_slide(self, file: str):
        if not file.startswith("ppt/slides/slide"):
            raise ValueError(f"{file} is not a slide")
        rel = f"ppt/slides/_rels/{file.split('/')[-1]}.rels"
        fp, frel = await asyncio.gather(self.open(file), self.open(rel))
        with fp, frel:
            return await Slide().from_bufferedIO(fp, frel)

    async def slides(self):
        if self._zipfile is None:
            raise ValueError
        tasks = [
            self.get_slide(file)
            for file in self._zipfile.namelist()
            if file.startswith("ppt/slides/slide")
        ]
        return await asyncio.gather(*tasks)

    async def get_tables(self) -> list[DataFrame]:
        task = [slide.get_tables() for slide in await self.slides()]
        res = await asyncio.gather(*task)
        return sum(res, [])

    @overload
    async def get_image(self, xref: str):
        '''读取二进制图片数据'''
        fp = await self.open(xref)
        return cv2.imdecode(np.fromstring(fp, dtype=np.uint8), 1)

    @overload
    async def get_image(self, index: int):
        bs = BeautifulSoup(slide, features="xml")
        title = bs.find("p:ph", type="title")
        if title and title.parent.parent.parent.text == pic:
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


class Slide:
    '''
    异步风格Slide操作类, 支持`async`/`await`
    '''

    def __init__(self):
        self._bs = None
        self._rel = None
        self.ns = {"a": ""}

    async def from_bufferedIO(self, file, rel):
        t_file = asyncio.to_thread(ET.parse, file)
        t_rel = asyncio.to_thread(ET.parse, rel)
        self._bs, self._rel = await asyncio.gather(t_file, t_rel)
        return self

    async def get_tables(self) -> list[DataFrame]:
        '''Get standard tables in slide'''
        res = []
        for table_tag in self._bs.findall(".//a:graphicData", self.ns):
            rows = table_tag.findall(".//a:tr", self.ns)
            if not rows or len(rows) < 2:
                continue
            heads = ["".join(col.itertext())
                     for col in rows[0].findall(".//a:tc", self.ns)]
            data = [["".join(col.itertext()) for col in row.findall(
                ".//a:tc", self.ns)] for row in rows[1:]]
            res.append(DataFrame(data, columns=heads))
        return res

    async def get_image_names(self):
        # 这样获取的图片可能存在显示与原图片发生变换
        relations = self._rel.findall(".//Relationship")
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
