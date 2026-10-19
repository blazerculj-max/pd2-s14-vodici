"""Prenese PD2 wiki strani s skilli (predpogoji) in cube recepti v data/wiki/<stran>.txt ter strani s predmeti v data/wiki/html/."""
import json
import os
import re
import subprocess
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "wiki")
API = "https://wiki.projectdiablo2.com/w/api.php"
PAGES = [f"All_{c}_Skills" for c in ["Amazon", "Assassin", "Barbarian", "Druid", "Necromancer", "Paladin", "Sorceress"]]
PAGES += ["Horadric_cube"]
ITEM_PAGES = ["All_Unique_Weapons", "All_Unique_Non-Weapons", "All_Set_Items", "All_Runewords", "Charms", "Class_Weapons"]


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "table", "dd", "dt"):
            self.out.append("\n")
        if tag in ("h2", "h3", "h4"):
            self.out.append("## ")
        if tag in ("td", "th"):
            self.out.append(" | ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def main():
    os.makedirs(OUT, exist_ok=True)
    for page in PAGES:
        url = f"{API}?action=parse&page={page}&prop=text&format=json&formatversion=2&redirects=1"
        raw = subprocess.run(["curl", "-sL", "-m", "90", url], capture_output=True, text=True).stdout
        parser = Text()
        parser.feed(json.loads(raw)["parse"]["text"])
        txt = re.sub(r"[ \t]+", " ", "".join(parser.out))
        txt = re.sub(r"\n\s*\n+", "\n", txt)
        open(os.path.join(OUT, f"{page}.txt"), "w").write(txt)
        print(page, len(txt))
    os.makedirs(os.path.join(OUT, "html"), exist_ok=True)
    for page in ITEM_PAGES:
        url = f"{API}?action=parse&page={page}&prop=text&format=json&formatversion=2&redirects=1"
        raw = subprocess.run(["curl", "-sL", "-m", "90", url], capture_output=True, text=True).stdout
        json.loads(raw)  # preveri, da je veljaven JSON
        open(os.path.join(OUT, "html", f"{page}.json"), "w").write(raw)
        print(page, len(raw))


if __name__ == "__main__":
    main()
