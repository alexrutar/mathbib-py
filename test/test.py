from pathlib import Path
from mathbib.record import ArchiveRecord
from mathbib.citegen import generate_biblatex


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


# test_fail_load()
try:
    {}["hi"]
except KeyError as e:
    print(str(e))
