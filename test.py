# import time
# import random
# import asyncio

# from QCseek.model import *
# from QCseek.view import backup
# from QCseek.handle_old import update_ssl, update_pdf
from QCseek.sds_reader import pre_cut


if __name__ == "__main__":
    pre_cut("2.jpg", cut_bg=True)
