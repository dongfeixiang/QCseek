from ttkbootstrap import Treeview


class QCRow():
    def __init__(self, pid:str, sds, sec, lal):
        self.pid = pid
        self.sds = sds
        self.sec = sec
        self.lal = lal
    
    def values(self) -> list:
        sds = self.sds.purity if self.sds is not None else "N/A"
        sec = self.sec.monomer if self.sec is not None else "N/A"
        lal = self.lal.value if self.lal is not None else "N/A"
        return [self.pid, sds, sec, lal]

class QCTable(Treeview):
    def __init__(self, master):
        super().__init__(
            master,
            bootstyle = "dark",
            columns=[0, 1, 2, 3],
            show="headings",
            height=20)
        self._rows:dict[str, QCRow] = {}
        self.heading(0, text="蛋白编号")
        self.heading(1, text="SDS(%)")
        self.heading(2, text="SEC(%)")
        self.heading(3, text="LAL(EU/mg)")

    def insert_row(self, qcrow:QCRow):
        iid = self.insert(parent="", index="end", values=qcrow.values())
        self._rows[iid] = qcrow
        self.see(iid)
    
    def get_rows(self) -> list[QCRow]:
        iid_list = self.selection()
        return [self._rows[i] for i in iid_list]