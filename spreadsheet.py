import csv
import pathlib

def get_data():
    yield [
        "Chem length",
        "Time (seconds)",
        "Success"
    ]
    for file in pathlib.Path("data").glob("*.txt"):
        with open(file) as f:
            text = f.read().split("\n", 5)
            yield [
                text[0],
                text[1],
                "0" if "failed" in str(file) else "1"
            ]

with open("out.csv", "w", newline='') as f:
    csv.writer(f).writerows(get_data())
