import shutil
from pathlib import Path
from ttkbootstrap import (
    Window, Button, Entry, Frame, StringVar, Progressbar
    )
from ttkbootstrap.dialogs.dialogs import Messagebox
from ttkbootstrap.window import Toplevel
from tkinter.filedialog import askdirectory

from model import SDS, SEC, LAL
from view import update_ssl, clean
from component import QCTable, QCRow


class ProgressBox(Toplevel):
    def __init__(self):
        super().__init__()
        self.create_body()
        self.place_window_center()
        self.overrideredirect(True)

    def create_body(self):
        self.pro = Progressbar(
            self, 
            bootstyle="success", 
            mode="indeterminate",
            maximum=20,
        )
        self.pro.pack()
        self.pro.start()


class App(Window):
    def __init__(self):
        super().__init__(themename="yeti")
        self.create_widget()
        self.place_window_center()

    def create_widget(self):
        cmd_panel = Frame(self)
        cmd_panel.pack()
        self.search_value = StringVar(self)
        Entry(cmd_panel, textvariable=self.search_value).pack(side="left")
        Button(cmd_panel, text="搜索", command=self.find_by_pid).pack(side="left")
        Button(cmd_panel, text="更新", command=self.update_database).pack(side="left")
        Button(cmd_panel, text="清洗", command=self.clean_database).pack(side="left")
        Button(cmd_panel, text="导出", command=self.export).pack(side="left")

        self.table = QCTable(self)
        self.table.pack(fill="both", expand="yes")
    
    def find_by_pid(self):
        pid = self.search_value.get()
        if not pid:
            return
        sds_query = SDS.select(SDS.purity, SDS.source).where(SDS.pid==pid)
        sec_query = SEC.select(SEC.monomer, SEC.source, SEC.attach).where(SEC.pid==pid)
        lal_query = LAL.select(LAL.value, LAL.source).where(LAL.pid==pid)
        if len(sds_query)>1 or len(sec_query)>1 or len(lal_query)>1:
            Messagebox.show_info("More", "More", self)
        sds = sds_query.get() if sds_query else None
        sec = sec_query.get() if sec_query else None
        lal = lal_query.get() if lal_query else None
        self.table.insert_row(QCRow(pid, sds, sec, lal))
    
    def update_database(self):
        # pro = ProgressBox()
        update_ssl()
        # pro.destroy()

    def clean_database(self):
        clean(SDS)
        clean(SEC)
        clean(LAL)

    def export(self):
        selected = self.table.get_rows()
        files = []
        for row in selected:
            if row.sds is not None:
                files.append(row.sds.source.pathname)
            if row.sec is not None:
                files.append(row.sec.source.pathname)
                if row.sec.attach is not None:
                    files.append(row.sec.attach.pathname)
            if row.lal is not None:
                files.append(row.lal.source.pathname)
        folder = askdirectory()
        for file in files:
            shutil.copy(file, folder)

if __name__ == "__main__":
    app = App()
    app.mainloop()