from model import *
import asyncio
import time
from tqdm.asyncio import tqdm_asyncio

async def main():
    sds1 = SDS.get(SDS.id==100)
    sds2 = SDS.get(SDS.id==110)
    sds3 = SDS.get(SDS.id==120)
    tasks = [SDS.from_ppt(s.source) for s in [sds1, sds2, sds3]]
    await tqdm_asyncio.gather(*tasks)

if __name__ == "__main__":
    t1 = time.perf_counter()
    asyncio.run(main())
    print(time.perf_counter()-t1)