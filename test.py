import cv2
from qcseek.sds_reader import pre_cut, gel_crop
from qcseek.model import SDS
from qcseek.pptx import PPTX
import asyncio
from schedule.dialog import get_sys_chrome


async def main():
    sds = SDS.get(SDS.pid == "P97391")
    async with PPTX(sds.source.shortpathname) as ppt:
        await ppt.slides()

if __name__ == "__main__":
    print(get_sys_chrome())
