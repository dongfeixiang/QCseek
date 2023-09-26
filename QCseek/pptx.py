import asyncio
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import cv2
import numpy as np
from pandas import DataFrame


class Slide:
    '''
    异步风格Slide操作类, 支持`async`/`await`
    '''

    def __init__(self):
        self._bs = None
        self._rel = None
        self.ns = {}
        self.rns = {}

    async def from_bufferedIO(self, file, rel):
        '''从字节流中初始化解析器'''
        # 读取XML命名空间
        ns_coro = asyncio.to_thread(ET.iterparse, file, ["start-ns"])
        rns_coro = asyncio.to_thread(ET.iterparse, rel, ["start-ns"])
        ns, rns = await asyncio.gather(ns_coro, rns_coro)
        self.ns = dict([i for _, i in ns])
        self.rns = dict([i for _, i in rns])
        # 恢复文件指针，重新初始化ET解析器
        file.seek(0)
        rel.seek(0)
        t_file = asyncio.to_thread(ET.parse, file)
        t_rel = asyncio.to_thread(ET.parse, rel)
        self._bs, self._rel = await asyncio.gather(t_file, t_rel)
        return self

    def get_tables(self) -> list[DataFrame]:
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

    def get_image_names(self):
        # 这样获取的图片可能存在显示与原图片发生变换
        relations = self._rel.findall(".//Relationship", self.rns)
        image_list = [
            r.get("Target").replace("..", "ppt")
            for r in relations
            if "media" in r.get("Target")
        ]
        return image_list

    def get_index(self):
        '''获取标题序号'''
        title = self._bs.find(".//p:ph[@type='title']/../../..", self.ns)
        if title is None:
            return None
        try:
            return int("".join(title.itertext()).strip())
        except:
            return None


class PPTX:
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

    async def open(self, file: str):
        '''打开文件二进制IO流'''
        if self._zipfile is None:
            raise ValueError
        fp = await asyncio.to_thread(self._zipfile.open, file)
        return fp

    async def get_slide(self, file: str) -> Slide:
        if not file.startswith("ppt/slides/slide"):
            raise ValueError(f"{file} is not a slide")
        self._zipfile.extract(file)
        rel = f"ppt/slides/_rels/{file.split('/')[-1]}.rels"
        fp, frel = await asyncio.gather(self.open(file), self.open(rel))
        with fp, frel:
            return await Slide().from_bufferedIO(fp, frel)

    async def slides(self) -> list[Slide]:
        if self._zipfile is None:
            raise ValueError
        tasks = [
            self.get_slide(file)
            for file in self._zipfile.namelist()
            if file.startswith("ppt/slides/slide")
        ]
        return await asyncio.gather(*tasks)

    async def get_tables(self) -> list[DataFrame]:
        slides = await self.slides()
        tables = [slide.get_tables() for slide in slides]
        return sum(tables, [])

    async def get_image_by_name(self, xref: str):
        '''根据名称索引读取二进制图片数据'''
        fp = await self.open(xref)
        return cv2.imdecode(np.frombuffer(fp.read(), dtype=np.uint8), 1)

    async def get_image_by_index(self, index: int):
        '''根据序号索引读取二进制图片数据'''
        slides = await self.slides()
        for i in slides:
            if i.get_index() and i.get_index() == index:
                images = i.get_image_names()
                img_name = images[0] if len(images) == 1 else images[1]
                img = await self.get_image_by_name(img_name)
                return img


async def main():
    async with PPTX("sec.pptx") as ppt:
        slides = await ppt.slides()
        index = slides[3].get_index()
        print(index)

if __name__ == "__main__":
    asyncio.run(main())