import sqlite3 as sql3

from xdg_base_dirs import xdg_data_home


class IndexDatabase:
    def __init__(self):
        self.db_path = xdg_data_home() / "mathbib" / "index.db"
        self.keys = ("arxiv", "zbl")
        if not self.db_path.exists():
            con = sql3.connect(self.db_path)
            con.execute("CREATE TABLE records(key, id, title, author, year, file)")
