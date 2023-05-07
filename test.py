from zbrecord import cite_file_search, BaseRecord, ArXiV, ZBmath
from pathlib import Path

# print(BaseRecord(url="hello"))
print(cite_file_search(Path("example.tex")))

# print(BaseRecord.from_doi("10.54330/afm.120529"))
# print(BaseRecord.from_arxiv("2209.00348"))
# print(BaseRecord.from_zbl("0929.28007"))
