#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成画廊首页 index.html

扫描 库-作者王伯伦制/<组>/<动效>.html，自动生成根目录的 index.html。

你只管把新的 .html 放进 库-作者王伯伦制/ 下的任意组里，剩下的交给它：
- 名字：优先用 画廊文案.json 里写的中文名，没写就用页面 <title>
- 一句话：优先用 画廊文案.json，没写就留空（卡片只剩名字）
- 版本徽标：同一组里同名带 vX.Y 的文件自动比较，最高版本标「最新」，其余标「旧版」并置灰
- 排序：按文件名自然排序（1、2、3…数字在前，字母在后）

用法：
    python tools/生成画廊.py
然后 push，GitHub Pages 会自动重建。

作者：王伯伦 · 本脚本由 AI 协助编写
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB_NAME = "库-作者王伯伦制"
LIB = ROOT / LIB_NAME
COPY_FILE = ROOT / "画廊文案.json"
OUT = ROOT / "index.html"

TITLE_RE = re.compile(r"<title>\s*(.*?)\s*</title>", re.S | re.I)
VER_RE = re.compile(r"^(.*?)(?:[-\s]*v(\d+(?:\.\d+)*))?$", re.I)


def nat_key(s: str):
    """自然排序：把数字段按数值比较，数字/字母在前，中文在后。"""
    parts = re.split(r"(\d+(?:\.\d+)*)", s)
    key = []
    for p in parts:
        if not p:
            continue
        if re.fullmatch(r"\d+(?:\.\d+)*", p):
            key.append((0, float(p)))
        else:
            key.append((1, p))
    return key


def read_text(p: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return p.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def clean_title(raw: str) -> str:
    t = re.sub(r"\s*·\s*王伯伦原创.*$", "", raw).strip()
    t = re.sub(r"\s*—\s*王伯伦原创.*$", "", t).strip()
    t = t.replace(" — ", " · ").replace("—", "·")
    return re.sub(r"\s+", " ", t).strip()


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def scan():
    groups = {}
    for sub in sorted([d for d in LIB.iterdir() if d.is_dir()], key=lambda d: nat_key(d.name)):
        items = []
        for f in sorted([f for f in sub.iterdir() if f.is_file() and f.suffix.lower() == ".html"],
                        key=lambda f: nat_key(f.stem)):
            if f.name.startswith("_"):
                continue
            raw_title = ""
            try:
                m = TITLE_RE.search(read_text(f))
                if m:
                    raw_title = m.group(1)
            except Exception:
                pass
            ver_m = VER_RE.match(f.stem)
            base = ver_m.group(1) if ver_m else f.stem
            ver = ver_m.group(2) if ver_m and ver_m.group(2) else "1"
            items.append({
                "file": f.name,
                "rel": f"{sub.name}/{f.name}",
                "title": clean_title(raw_title) if raw_title else f.stem,
                "base": base,
                "ver": tuple(int(x) for x in ver.split(".")),
                "version_text": ("v" + ver) if ver_m and ver_m.group(2) else "",
            })
        if items:
            groups[sub.name] = items
    return groups


def apply_copy(groups, copy):
    texts = copy.get("文案", {})
    for g, items in groups.items():
        # 同一组内 base 相同的算一个族，最高版本标最新
        fams = {}
        for it in items:
            fams.setdefault(it["base"], []).append(it)
        for base, fam in fams.items():
            if len(fam) > 1:
                top = max(fam, key=lambda x: x["ver"])
                for it in fam:
                    it["badge"] = "最新" if it is top else "旧版"
                    it["dim"] = it is not top
            else:
                fam[0]["badge"] = ""
                fam[0]["dim"] = False

    for it in [i for items in groups.values() for i in items]:
        c = texts.get(it["rel"])
        if c:
            it["name"] = c.get("name") or it["title"]
            it["desc"] = c.get("desc", "")
            if "badge" in c:
                it["badge"] = c["badge"]
            if "dim" in c:
                it["dim"] = bool(c["dim"])
        else:
            it["name"] = it["title"]
            it["desc"] = ""


CSS = """
  :root { color-scheme: dark; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: radial-gradient(120% 80% at 50% 0%, #0d141d 0%, #06080d 55%, #020409 100%);
    color: #dbe7f5;
    font-family: "Segoe UI", "Microsoft YaHei", system-ui, sans-serif;
    min-height: 100vh;
    padding: 64px 28px 80px;
  }
  .wrap { max-width: 1120px; margin: 0 auto; }
  header { margin-bottom: 54px; }
  .kicker { font-size: 12px; letter-spacing: 4px; color: rgba(140, 190, 230, 0.55); }
  h1 { margin-top: 14px; font-size: 40px; font-weight: 800; letter-spacing: 1px; color: #eaf4ff; }
  .lead { margin-top: 16px; font-size: 15px; line-height: 1.9; color: rgba(200, 220, 240, 0.72); max-width: 660px; }
  .lead em { color: #8fe6ff; font-style: normal; }
  section { margin-top: 46px; }
  .sec-head { display: flex; align-items: baseline; gap: 14px; border-bottom: 1px solid rgba(120, 160, 200, 0.16); padding-bottom: 10px; }
  .sec-head h2 { font-size: 19px; font-weight: 700; letter-spacing: 2px; color: #cfe6fb; }
  .sec-head span { font-size: 12px; letter-spacing: 1px; color: rgba(150, 180, 210, 0.5); }
  .grid { display: grid; gap: 14px; margin-top: 20px; grid-template-columns: repeat(auto-fill, minmax(258px, 1fr)); }
  a.card {
    display: block; text-decoration: none; color: inherit;
    padding: 18px 18px 16px; border-radius: 12px;
    background: linear-gradient(160deg, rgba(28, 38, 52, 0.72), rgba(11, 15, 22, 0.82));
    border: 1px solid rgba(120, 160, 200, 0.14);
    transition: transform 0.18s ease-out, border-color 0.18s ease-out, box-shadow 0.18s ease-out;
  }
  a.card:hover {
    transform: translateY(-3px);
    border-color: rgba(125, 249, 255, 0.42);
    box-shadow: 0 14px 34px rgba(0, 0, 0, 0.46), 0 0 24px rgba(90, 200, 255, 0.14);
  }
  a.card .name { font-size: 15px; font-weight: 700; color: #e8f4ff; letter-spacing: 0.5px; }
  a.card .name .tag {
    font-size: 10px; font-weight: 500; letter-spacing: 1px;
    padding: 2px 6px; margin-left: 8px; border-radius: 4px;
    color: rgba(150, 240, 255, 0.9); border: 1px solid rgba(125, 249, 255, 0.32);
    vertical-align: 2px;
  }
  a.card .desc { margin-top: 9px; font-size: 12.5px; line-height: 1.75; color: rgba(190, 210, 232, 0.62); }
  a.card .go { margin-top: 12px; font-size: 11px; letter-spacing: 2px; color: rgba(125, 249, 255, 0.72); }
  a.card.dim { opacity: 0.62; }
  a.card.dim .go { color: rgba(150, 170, 190, 0.5); }
  footer { margin-top: 66px; padding-top: 22px; border-top: 1px solid rgba(120, 160, 200, 0.12); font-size: 12px; line-height: 2; color: rgba(160, 185, 208, 0.5); }
  footer a { color: rgba(125, 249, 255, 0.6); text-decoration: none; }
"""


def build(groups, copy):
    order = copy.get("组顺序") or list(groups.keys())
    order = [g for g in order if g in groups] + [g for g in groups if g not in order]
    subs = copy.get("组副标题", {})

    total = sum(len(v) for v in groups.values())
    out = []
    out.append('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">')
    out.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.append('<title>表达的多元宇宙 · expression-multiverse</title>')
    out.append("<style>" + CSS + "</style>\n</head>\n<body>\n<div class=\"wrap\">\n")
    out.append(f"""  <header>
    <div class="kicker">EXPRESSION · MULTIVERSE</div>
    <h1>表达的多元宇宙</h1>
    <p class="lead">
      同一件事，不止一种表达方式。<br>
      这里放着 {total} 个<em>活的</em>界面动效——点开任意一个，它就在浏览器里跑起来，不是截图，不是摆件。
    </p>
  </header>
""")
    for g in order:
        items = groups[g]
        sub = subs.get(g, "")
        head_span = f"{len(items)} 件" + (f" · {sub}" if sub else "")
        out.append(f'  <section>\n    <div class="sec-head"><h2>{esc(g)}</h2><span>{esc(head_span)}</span></div>\n    <div class="grid">\n')
        for it in items:
            href = LIB_NAME + "/" + it["rel"]
            cls = "card dim" if it["dim"] else "card"
            tag = f'<span class="tag">{esc(it["badge"])}</span>' if it["badge"] else ""
            desc = f'\n        <div class="desc">{esc(it["desc"])}</div>' if it["desc"] else ""
            out.append(f'      <a class="{cls}" href="{esc(href)}">\n'
                       f'        <div class="name">{esc(it["name"])}{tag}</div>{desc}\n'
                       f'        <div class="go">打开 →</div>\n'
                       f'      </a>\n')
        out.append("    </div>\n  </section>\n")

    out.append("""  <footer>
    作者 王伯伦原创制作 · 代码以 Apache-2.0 授权（见 <a href="https://github.com/132wbl/expression-multiverse/blob/main/LICENSE">LICENSE</a>），拿走改都行，保留出处即可。<br>
    仓库：<a href="https://github.com/132wbl/expression-multiverse">github.com/132wbl/expression-multiverse</a>
    · 每个动效都是单文件（HTML+CSS+JS），双击即开，也能直接 iframe 嵌进别人的页面。
  </footer>

</div>
</body>
</html>
""")
    return "".join(out)


def main():
    if not LIB.is_dir():
        print(f"找不到库目录：{LIB}")
        return 1
    copy = {}
    if COPY_FILE.is_file():
        try:
            copy = json.loads(read_text(COPY_FILE))
        except Exception as e:
            print(f"画廊文案.json 解析失败（先按无文案处理）：{e}")
    groups = scan()
    if not groups:
        print("库里没有 html，什么都没改。")
        return 1
    apply_copy(groups, copy)
    html = build(groups, copy)
    old = read_text(OUT) if OUT.is_file() else ""
    if old == html:
        print("index.html 已是最新，无需改动。")
        return 0
    OUT.write_text(html, encoding="utf-8", newline="\n")
    total = sum(len(v) for v in groups.values())
    print(f"已生成 index.html：{len(groups)} 组 / {total} 个动效")
    for g, items in groups.items():
        print(f"  - {g}：{len(items)} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
