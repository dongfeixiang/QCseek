from shutil import copy
from ttkbootstrap import (
    Window, Button, Entry, Frame, StringVar, Progressbar, Label
    )
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.window import Toplevel
from tkinter.filedialog import askdirectory

from model import SDS, SEC, LAL
from view import update_ssl, clean, extract_sds, extract_sds_lane, extract_sec
from component import QCTable, QCRow
from sds_reader import pre_cut, gel_crop
import cv2
import numpy as np
import os
import time
from threading import Thread
import asyncio

class ProgressBox(Toplevel):
    def __init__(self):
        super().__init__(title="任务",size=(300,80), overrideredirect=True)
        self.create_body()
        self.place_window_center()

    def create_body(self):
        self.winframe = Frame(self, relief="groove")
        self.winframe.pack(fill="both", expand=True)
        self.lb = Label(self.winframe)
        self.lb.pack(pady=5)
        self.pro = Progressbar(
            self.winframe, 
            bootstyle="success", 
            mode="indeterminate",
            maximum=20,
        )
        self.pro.pack()
        self.pro.start()
    
    def write(self, text:str):
        self.lb.config(text=text)


class App(Window):
    def __init__(self):
        super().__init__(themename="yeti")
        self.title("QCseek")
        self.create_widget()
        self.place_window_center()

    def create_widget(self):
        cmd_panel = Frame(self)
        cmd_panel.pack()
        self.search_value = StringVar(self)
        Entry(cmd_panel, textvariable=self.search_value).pack(side="left")
        Button(cmd_panel, text="搜索", command=self.find_by_pid).pack(side="left")
        Button(cmd_panel, text="更新", command=self.update_database).pack(side="left")
        Button(cmd_panel, text="清洗", command=self.clean_database, state="disabled").pack(side="left")
        Button(cmd_panel, text="导出", command=self.export).pack(side="left")
        Button(cmd_panel, text="CoA", command=self.generate_coa).pack(side="left")

        self.table = QCTable(self)
        self.table.pack(fill="both", expand="yes")
    
    def find_by_pid(self):
        pid = self.search_value.get().strip()
        if not pid:
            return
        sds_query = SDS.select().where(SDS.pid==pid)
        sec_query = SEC.select().where(SEC.pid==pid)
        lal_query = LAL.select().where(LAL.pid==pid)
        if len(sds_query)>1 or len(sec_query)>1 or len(lal_query)>1:
            Messagebox.show_info("More", "More", self)
        sds = sds_query.get() if sds_query else None
        sec = sec_query.get() if sec_query else None
        lal = lal_query.get() if lal_query else None
        self.table.insert_row(QCRow(pid, sds, sec, lal))
    
    def update_database(self):
        self.pro = ProgressBox()
        t = Thread(target=self.asyncThread, args=(lambda:self.pro.destroy(),), daemon=True)
        t.start()
    
    def asyncThread(self, callback):
        asyncio.run(update_ssl())
        callback()

    def clean_database(self):
        clean(SDS)
        clean(SEC)
        clean(LAL)

    def export(self):
        selected = self.table.get_rows()
        files = {}
        for row in selected:
            files[row.pid] = []
            if row.sds is not None:
                files[row.pid].append(row.sds.source.pathname)
            if row.sec is not None:
                files[row.pid].append(row.sec.source.pathname)
                if row.sec.attach is not None:
                    files[row.pid].append(row.sec.attach.pathname)
            if row.lal is not None:
                files[row.pid].append(row.lal.source.pathname)
        folder = askdirectory()
        for pid, v in files.items():
            for file in v:
                if not os.path.exists(f"{folder}/{pid}"):
                    os.mkdir(f"{folder}/{pid}")
                copy(file, f"{folder}/{pid}")

    def generate_coa(self):
        self.pro = ProgressBox()
        task = Thread(target=self.pplog, daemon=True)
        task.start()
    
    def pplog(self):
        self.pro.write("hello")
        time.sleep(1)
        self.pro.write("world")
        self.pro.destroy()
        # selected = self.table.get_rows()
        # for row in selected:
        #     # if row.sds is not None:
        #     #     sds_img, lane = extract_sds(row.sds)
        #     #     sds_img = extract_sds_lane(sds_img, lane)
        #     #     cv2.imwrite(f"{row.sds.pid}/SDS/sds.png", sds_img)
        #     if row.sec is not None:
        #         sec_img = extract_sec(row.sec)
        #         print(sec_img)

if __name__ == "__main__":
    app = App()
    app.mainloop()