import cv2
from QCseek.sds_reader import pre_cut, gel_crop
from QCseek.model import SDS
from QCseek.pptx import PPTX
import asyncio


async def main():
    sds = SDS.get(SDS.pid == "P97391")
    async with PPTX(sds.source.shortpathname) as ppt:
        await ppt.slides()

if __name__ == "__main__":
    asyncio.run(main())