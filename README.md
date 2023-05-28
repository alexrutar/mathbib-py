# MathBib
MathBib is a mathematics BibLaTeX bibliography manager.
Jump to:
- [Installation and basic usage](#installation-and-basic-usage)
- [Finer details](#some-finer-details)

## Installation and basic usage
First, ensure that `mbib` is installed with
```sh
pip install mathbib
```
This installs the `mbib` command-line interface.
The first useful subcommand is `mbib get`.
For instance, running
```sh
mbib get bibtex arxiv:1212.1873
```
will retrieve the arxiv record at [https://arxiv.org/abs/1212.1873](https://arxiv.org/abs/1212.1873).
If you check the output, you will notice that it actually returns
```bib
@article{arxiv:1212.1873,
  author = {Hochman, Michael},
  eprint = {1337.28015},
  eprinttype = {zbl},
  journal = {Ann. Math.},
  language = {English},
  number = {2},
  pages = {773--822},
  publisher = {Annals of Mathematics},
  title = {On self-similar sets with overlaps and inverse theorems for entropy},
  volume = {180},
  year = {2014}
}
```
This contains more information than what can be found on arxiv!
In general `mbib` will attempt to search multiple locations for records to build the most updated citation possible.

Generating records from command-line arguments is nice, but a much more common use case is to generate records corresponding to a file.
Suppose you have a file `doc.tex` containing the contents
```tex
\documentclass{article}
\usepackage{biblatex}
\addbibresource{doc.bib}
\begin{document}
This document references an article \cite{arxiv:1212.1873}.
It also contains more references \cite{zbl:1251.28008, doi:10.4007/annals.2019.189.2.1}.
\printbibliography
\end{document}
```
Simply run
```sh
mbib generate doc.tex > doc.bib
```
to build the `.bib` file, and compile.

Of course, it can be somewhat inconvenient to remember a large number of citation keys, especially ones that are designed to be machine-readable.
An easy fix here is to create aliases.
Let's define a few:
```sh
mbib alias add Hoc2014 arxiv:1212.1873
mbib alias add HocShm2012 zbl:1251.28008
mbib alias add Shm2019 doi:10.4007/annals.2019.189.2.1
```
We could now instead write our file  as
```tex
\documentclass{article}
\usepackage{biblatex}
\addbibresource{doc.bib}
\begin{document}
This document references an article \cite{Hoc2014}.
It also contains more references \cite{HocShm2012, Shm2019}.
\printbibliography
\end{document}
```
Remember to regenerate the `doc.bib` file with `mbib generate doc.tex > doc.bib` (the keys need to be updated), and the file will compile!
Aliases also work as command line arguments anywhere a `key:id` is expected.

Suppose you have been working on the above TEX document for a while, and now you want to cite a specific theorem from the paper `Hoc2014`.
Simply run
```sh
mbib file open Hoc2014
```
to open the PDF file associated with the resource.
This will automatically download a PDF resource for the file (if `mbib` can find one online) and then open it.
The PDF file is also saved locally, so the next time you run this command, you do not need an internet connection.

Of course, if `mbib` cannot find a resource for your file, you can also add one yourself.
```sh
mbib file add Hoc2014 path/to/file.pdf
```

Finally, if you have loaded a record but there are mistakes (for instance, improperly formatted LaTeX titles), you can apply local modifications which will always be applied when requesting the record.
Edit the local record with, for example,
```
mbib file open zbl:1251.28008
```
There are also other features implemented: either read more below, or run `mbib --help` and `mbib <subcommand> --help` for more information.

## Remote and local records
Internally, whenever you request a new record, MathBib searches a few online data repositories for the information associated with the record.
Currently, the following `KEY:` types are supported
- `local:` (WARNING: not supported) internal local records
- `zbl:` [zbMATH Identifiers](https://zbmath.org/)
- `doi:` [Digital Object Identifier](https://doi.org)
- `mr:` (WARNING: not supported) [MathSciNet](https://mathscinet.ams.org)
- `zbmath:` [zbMath Internal Identifier](https://oai.zbmath.org/)
- `arxiv:` [arXiv Identifier](https://arxiv.org)
- `isbn:` [International Standard Book Number](https://en.wikipedia.org/wiki/ISBN).
- `ol:` [Open Library](https://openlibrary.org/) resource identifiers.

The requests to the various sources are cached in `$XDG_CACHE_HOME/mathbib`.
In particular, the first search will be slow, but afterwards the request will resolve quickly.

You can see all the information collected by MathBib by running, for instance,
```
mbib get json arxiv:1212.1873
```
Note that MathBib also has an internal notion of record priority.
Local modifications of records have the highest priority, and otherwise the priority is precisely as specified in the list above.
For instance, if you run `mbib show arxiv:1212.1873`, your web browser will open a record on zbMATH.
If you view the corresponding JSON record, you will see the `zbl:` entry has the highest priority.


# Contributing and future improvements
MathBib is still under active development!
Some planned features include:

1. Rework the code for remote record searching and parsing.
2. Asynchronous requests for faster record downloading.
3. Nicer printing and viewing using [rich](https://rich.readthedocs.io/en/stable/introduction.html).
