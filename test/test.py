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


test_file_citations()
# print(HumanName("Kenneth J. Falconer").__repr__)
# print(ArchiveRecord.from_arxiv("2206.06921").as_local_dict())


# TODO next:
# - bibtex generation from record
# - save records locally, and search there first
# - manually editing records?
