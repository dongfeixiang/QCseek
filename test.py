import time

from QCseek.handle_old import collect_files


if __name__ == "__main__":
    t1 = time.perf_counter()
    # asyncio.run(collect_files())
    collect_files()
    print(time.perf_counter()-t1)
