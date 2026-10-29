"""Step 7: blog post and meta (release/blog/), Zenodo folder and meta (release/zenodo/). Run: python3 code/07_release.py"""
import json, os, re, shutil, zipfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
def get(path):
    if path in R.get("page", {}): return R["page"][path]
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def sub(m):
    path, _, fm = m.group(1).partition("|"); v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    return str(v)
t = open(os.path.join(ROOT, "code", "blog_template.html")).read()
imgs = re.findall(r"^\{\{IMG\|.*\}\}$", t, re.M)
for i, line in enumerate(imgs): t = t.replace(line, f"@@IMG{i}@@")
t = re.sub(r"\{\{([^}]+)\}\}", sub, t)
for i, line in enumerate(imgs):
    t = t.replace(f"@@IMG{i}@@", '<!-- wp:image {"sizeSlug":"full"} -->\n<figure class="wp-block-image size-full">' + line + "</figure>\n<!-- /wp:image -->")
B = os.path.join(ROOT, "release", "blog"); open(os.path.join(B, "post.html"), "w").write(t)
for line in imgs: assert os.path.exists(os.path.join(B, line.split("|")[1])), line
words = len(re.sub(r"<[^>]+>|\{\{IMG[^}]*\}\}", " ", t).split())
hm = R["hm"]
json.dump(dict(title="High Street or Main Street? The UK's street-name divide", slug="street-names",
    excerpt=f"I sorted all {R['meta']['n_streets']:,} named streets in the UK by name. High Street rules the towns, Main Street the villages of Scotland, Northern Ireland, the East Midlands and Yorkshire, and every region has its own street words.",
    seo_description=f"Where High Street gives way to Main Street: all {R['meta']['n_streets']:,} UK street names mapped, from Wynd and Brae to Loke, Garth and Chare.",
    tags=["street names", "place names", "maps", "dialect", "Ordnance Survey", "OpenStreetMap", "UK", "data"],
    header_alt=f"Social card with two street signs reading High Street (black on white) and Main Street (white on blue), the text '{hm['uk']['high']:,} High Streets, {hm['uk']['main']:,} Main Streets', and a map of the UK in 20 km squares, red across southern England and Wales and blue across Scotland, Northern Ireland and a belt from Leicestershire to Yorkshire."),
    open(os.path.join(B, "meta.json"), "w"), indent=1, ensure_ascii=False)
# Zenodo
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
PDF = "Hotham_High_Street_or_Main_Street.pdf"
shutil.copy(os.path.join(ROOT, "release", PDF), Z)
for f in ["councils.csv", "cells_10km.csv", "regional_words.csv", "name_counts.csv.gz", "results.json"]: shutil.copy(os.path.join(ROOT, "data", f), Z)
zp = os.path.join(Z, "street-names_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ["code", "data"]:
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn: zf.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), ROOT))
    for f in ["README.md", "LICENSE"]: zf.write(os.path.join(ROOT, f), f)
tex = open(os.path.join(ROOT, "release", "paper", "Hotham_High_Street_or_Main_Street.tex")).read()
ab = re.search(r"\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("\\", "")
json.dump(dict(title="High Street or Main Street? The United Kingdom's Street-Name Divide",
    description_html=f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/street-names/. Data and code: https://github.com/Tristan-Hotham/street-names. Blog post: to follow.</p>",
    keywords=["street names", "odonymy", "place names", "dialect geography", "OS Open Names", "OpenStreetMap", "United Kingdom", "High Street", "open data", "data visualisation"],
    licence="cc-by-4.0",
    related=[dict(identifier="https://github.com/Tristan-Hotham/street-names", relation="issupplementedby", resource_type="software"),
             dict(identifier="https://maps.tristanhotham.com/street-names/", relation="issupplementedby", resource_type="other"),
             dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
             dict(identifier="https://www.openstreetmap.org", relation="isderivedfrom", resource_type="dataset"),
             dict(identifier="https://github.com/onsvisual/uk-topojson", relation="isderivedfrom", resource_type="dataset")]),
    open(os.path.join(Z, "meta.json"), "w"), indent=1, ensure_ascii=False)
print("blog words", words, "abstract words", len(ab.split()), "zip", os.path.getsize(zp))
