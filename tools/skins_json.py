#!/usr/bin/env python3
"""Write ios/Weatherglass/skins.json from the Android skin list (skin/Skin.kt),
so both apps have the same skins, colors and groups.

  python3 tools/skins_json.py
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "app", "src", "main", "java", "com", "peerloom", "weatherglass", "skin", "Skin.kt")
DST = os.path.join(HERE, "..", "ios", "Weatherglass", "skins.json")
FIELDS = ["bgTop", "bgBottom", "card", "text", "subtle", "accent", "icon"]
DEFAULTS = {"alert": "0xFFB3261E", "alertMild": "0xFFB26A00", "alertText": "0xFFFFFFFF"}


def split_args(s):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def call_body(text, start):
    """The text inside the parentheses that open at text[start]."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    raise ValueError("unbalanced")


def color(v):
    return "#" + v.replace("0x", "")[0:2] + v.replace("0x", "")[2:]  # #AARRGGBB


def palette(body):
    args = split_args(body)
    p = {}
    for i, a in enumerate(args):
        if "=" in a:
            k, v = [x.strip() for x in a.split("=", 1)]
            p[k] = v
        else:
            p[FIELDS[i]] = a
    for k, v in DEFAULTS.items():
        p.setdefault(k, v)
    p.setdefault("alertMildText", p["alertText"])
    return {k: color(v) for k, v in p.items()}


def main():
    text = re.sub(r"//[^\n]*", "", open(SRC).read())
    skins = {}
    for m in re.finditer(r"val (\w+) = Skin\(", text):
        body = call_body(text, m.end() - 1)
        args = split_args(body)
        s = {}
        for a in args:
            k, v = [x.strip() for x in a.split("=", 1)]
            if k in ("light", "dark"):
                s[k] = palette(call_body(v, v.index("(")))
            elif k in ("corner", "miniBelow"):
                s[k] = int(v)
            elif k in ("upperLabels", "followsSystem"):
                s[k] = v == "true"
            elif k == "font":
                s[k] = v.split(".")[-1].lower()
            else:
                s[k] = v.strip('"')
        s.setdefault("dark", s["light"])
        s.setdefault("font", "sans")
        s.setdefault("corner", 20)
        s.setdefault("upperLabels", False)
        s.setdefault("followsSystem", False)
        s.setdefault("miniBelow", 40)
        skins[m.group(1)] = s
    groups = []
    gm = re.search(r"val groups = listOf\((.*?)\n    \)", text, re.S)
    for name, members in re.findall(r'"([^"]+)" to listOf\(([^)]*)\)', gm.group(1)):
        groups.append({"name": name, "skins": [skins[x.strip()]["id"] for x in members.split(",") if x.strip()]})
    am = re.search(r"val all = listOf\((.*?)\)", text, re.S)
    order = [skins[x.strip()]["id"] for x in am.group(1).split(",") if x.strip()]
    by_id = {s["id"]: s for s in skins.values()}
    out = {"skins": [by_id[i] for i in order], "groups": groups}
    os.makedirs(os.path.dirname(DST), exist_ok=True)
    json.dump(out, open(DST, "w"), indent=1)
    print(len(order), "skins,", len(groups), "groups ->", DST)


if __name__ == "__main__":
    main()
