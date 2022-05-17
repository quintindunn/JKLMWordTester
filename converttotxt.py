import json


def convert(file):
    with open(file, 'r') as f:
        data = json.load(f)

    with open(file.replace(".json", '.txt'), 'w') as f:
        f.write("\n".join(data))


convert("correct.json")
convert("incorrect.json")
