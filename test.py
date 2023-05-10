from pathlib import Path
from nameparser import HumanName
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

from remote import arxiv_remote, zbmath_remote, zbl_remote
from zbrecord import ArchiveRecord, generate_file_citations


def test_record():
    hs_arxiv = "1302.5792"
    hs_zbl = "1409.11054"
    hs_zbmath = "6504096"
    # print("arxiv", arxiv_remote.load_record(hs_arxiv))
    # print("zbl", zbl_remote.load_record(hs_zbl))
    # print("zbmath", zbmath_remote.load_record(hs_zbmath))
    rec = ArchiveRecord.from_zbl(hs_zbl)
    print(rec.as_bibtex())


def test_file_citations():
    Path("out.bib").write_text(generate_file_citations(Path("example.tex")))


test_file_citations()
# print(HumanName("Kenneth J. Falconer").__repr__)
# print(ArchiveRecord.from_arxiv("2206.06921").as_local_dict())


# TODO next:
# - bibtex generation from record
# - save records locally, and search there first
# - manually editing records?
