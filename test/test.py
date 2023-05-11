from pathlib import Path
from mathbib.record import ArchiveRecord
from mathbib.citegen import generate_biblatex
from mathbib.index import list_records, generate_records_from_storage

# generate_records_from_storage()
for record in list_records():
    print(str(record))
    # print(" && ".join(record))


def test_record():
    # hs_arxiv = "1302.5792"
    hs_zbl = "1409.11054"
    # hs_zbmath = "6504096"
    # print("arxiv", arxiv_remote.load_record(hs_arxiv))
    # print("zbl", zbl_remote.load_record(hs_zbl))
    # print("zbmath", zbmath_remote.load_record(hs_zbmath))
    rec = ArchiveRecord.from_zbl(hs_zbl)
    print(rec.as_bibtex())


def test_file_citations():
    print(generate_biblatex(Path("example.tex")))


def test_fail_load():
    ArchiveRecord.from_arxiv("0593.59322")


# lost
# {
#   "title": "Real analysis",
#   "file": "/Users/alexrutar/Database/Zotero/Bruckner et al_1997_Real analysis2.pdf",
#   "zbl": "0872.26001"
# },
# {
#   "title": "Complex analysis",
#   "file": "/Users/alexrutar/.local/share/database/zotero_papers/S/2003/Stein_Shakarchi_2003_Complex analysis.pdf",
#   "zbl": "1020.30001"
# },
# {
#   "title": "Fourier analysis: an introduction",
#   "file": "/Users/alexrutar/.local/share/database/zotero_papers/S/2003/Stein_Shakarchi_2003_Fourier analysis.pdf",
#   "zbl": "1026.42001"
# },
