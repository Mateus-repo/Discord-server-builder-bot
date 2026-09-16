import re, json, sys

sys.stdout.reconfigure(encoding="utf-8")

def extract(path):
    with open(path, encoding="utf-8") as f:
        html = f.read()

    labels = re.findall(r'aria-label="([^"]+)"', html)
    structure = []
    loose = []
    cur = None
    TYPE_SUFFIX = re.compile(r"\s\((text|voice|forum|announcement|stage) channel\)$")

    for label in labels:
        lt = label.strip()
        if lt.endswith("(category)"):
            name = lt[: -len("(category)")].strip()
            cur = {"name": name, "channels": []}
            structure.append(cur)
        elif lt.endswith("(channel)"):
            m = TYPE_SUFFIX.search(lt)
            if not m:
                continue
            name_raw = lt[: m.start()].strip()
            name = re.sub(r"^(unread|muted|unmuted|selected|active), ?", "", name_raw).strip()
            if name.startswith(","):
                name = name[1:].strip()
            item = {"name": name, "type": m.group(1)}
            if cur is None:
                loose.append(item)
            else:
                cur["channels"].append(item)

    if loose:
        structure.insert(0, {"name": "📂 Sem Categoria", "channels": loose})
    return structure

parlor = extract(r"C:\Users\Strefiz\Documents\GitHub\Discord-server-builder-bot\server-template-parlor-html.txt")
with open(r"C:\Users\Strefiz\Documents\GitHub\Discord-server-builder-bot\server-template-parlor.json", encoding="utf-8") as f:
    parlor_expected = json.load(f)

print("parlor round-trip:", "OK" if parlor == parlor_expected else "MISMATCH")
if parlor != parlor_expected:
    a = json.dumps(parlor, ensure_ascii=False, indent=2).splitlines()
    b = json.dumps(parlor_expected, ensure_ascii=False, indent=2).splitlines()
    for x, y in zip(a, b):
        if x != y:
            print("GOT:", x)
            print("EXP:", y)
            break

cu = extract(r"C:\Users\Strefiz\Documents\GitHub\Discord-server-builder-bot\server-template-cu-html.txt")
with open(r"C:\Users\Strefiz\Documents\GitHub\Discord-server-builder-bot\server-template-cu.json", "w", encoding="utf-8") as f:
    json.dump(cu, f, indent=2, ensure_ascii=False)

print()
print(json.dumps(cu, ensure_ascii=False, indent=2))