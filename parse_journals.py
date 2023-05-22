from pathlib import Path

dct = {
    line.split(";")[0]: line.split(";")[1]
    for line in Path("journals.csv").read_text().split("\n")
    if len(line) >= 2
}
print(dct)
