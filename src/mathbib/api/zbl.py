import bibtexparser as bp


def url_builder(zbl: str) -> str:
    return f"https://zbmath.org/bibtex/{zbl}.bib"


def record_parser(result: str) -> dict:
    # parse bibtex string using bibtexparser
    parser = bp.bparser.BibTexParser()

    def customizations(record):
        return bp.customization.convert_to_unicode(
            bp.customization.page_double_hyphen(bp.customization.author(record))
        )

    parser.customization = customizations
    bibtex_parsed = bp.loads(result, parser=parser).entries[0]

    # capture some keys explicitly from the bibtex file
    captured = (
        "doi",
        "journal",
        "language",
        "issn",
        "number",
        "pages",
        "volume",
        "year",
        "zbmath",
    )

    # drop some keys from the bibtex file
    dropped = (
        "title",
        "fjournal",
        "zbmath",
        "ENTRYTYPE",
        "ID",
        "zbl",
        "keywords",
        "author",
    )

    extracted = {k: v for k, v in bibtex_parsed.items() if k in captured}
    additional = {
        # save any bibtex keys not captured or dropped
        "bibtex": {
            k: v
            for k, v in bibtex_parsed.items()
            if k not in captured and k not in dropped
        },
        "bibtype": bibtex_parsed["ENTRYTYPE"],
        "authors": bibtex_parsed["author"],
    }

    return {**extracted, **additional}