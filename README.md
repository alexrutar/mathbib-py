# MathBib
MathBib is a mathematics BibLaTeX bibliography manager.

## Installation and basic usage
First, ensure that `mbib` is installed with
```sh
pip install mathbib
```
This installs the `mbib` command-line interface.
The main operation is `mbib get`.
For instance, running
```sh
mbib get bibtex arxiv:1212.1873
```
will retrieve the arxiv record at [https://arxiv.org/abs/1212.1873](https://arxiv.org/abs/1212.1873).
However, if you check the output, you will notice that it actually returns
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

However, it can be somewhat inconvenient to remember a large number of citation keys.
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
For instance, you can view the PDF file associated with a record using
```sh
mbib file open Hoc2014
```
This will automatically download a PDF resource for the file (if `mbib` can find one online) and then open it.
The PDF file is also saved locally, so the next time you run this command, you do not need an internet connection.

There are some other features implemented: either read more below, or run `mbib --help` and `mbib <subcommand> --help` for more information.


## Some finer details
The record contains journal information, since `mbib` will also try to search for records in other repositories.
You can see the full collection of information obtained by `mbib` by running
```
mbib get json arxiv:1212.1873
```
You can also define aliases for records.
For instance,
```
mbib alias add 
```
