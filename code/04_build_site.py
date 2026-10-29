"""Step 4: fill code/page_template.html with numbers from data/results.json to make index.html.

A few page-level numbers derived from results.json are added to it under "page" first, so that
results.json holds every number on the page. Run: python3 code/04_build_site.py
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "data", "results.json")
R = json.load(open(RP))
PT = json.load(open(os.path.join(ROOT, "data", "page", "terms.json")))
n = R["meta"]["n_streets"]
gen = {g: c for g, c, sh in R["top_generic"]}
wales = R["meta"]["by_nation"]["Wales"]
R["page"] = dict(
    n_terms=sum(1 for t in PT["terms"] if R["terms"][t["key"]]["n"] > 0),
    gen_road_pct=gen["Road"] / n, gen_close_pct=gen["Close"] / n, gen_street_pct=gen["Street"] / n, gen_lane_pct=gen["Lane"] / n,
    wales_share=wales / n, lq_wales_max=n / wales, n_generics=None,
    retrieved_gb=R["meta"]["prep"]["gb_retrieved"][:10], retrieved_ni=R["meta"]["prep"]["ni_retrieved"][:10])
src = open(os.path.join(ROOT, "code", "01_prepare.py")).read()
gl = re.search(r"GENERICS = \[(.*?)\]", src, re.S).group(1)
R["page"]["n_generics"] = len(re.findall(r'"[^"]+"', gl))
R["hm"]["scotland_high_n"] = len(R["hm"]["scotland_high_more"])
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)

def get(path):
    if path in R["page"]: return R["page"][path]
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def f(m):
    path, _, fm = m.group(1).partition("|")
    v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}%"
    if fm == "pct1": return f"{v * 100:.1f}%"
    if fm == "f1": return f"{v:.1f}"
    return str(v)
t = open(os.path.join(ROOT, "code", "page_template.html")).read()
t = re.sub(r"\{\{([^}]+)\}\}", f, t)
terms_list = [dict(key=x["key"], label=x["label"], group=x["group"], note=x["note"], n=R["terms"][x["key"]]["n"]) for x in PT["terms"]]
emb = dict(meta=dict(n_streets=n), hm=dict(region=R["hm"]["region"], bands_gb=R["hm"]["bands_gb"], by_kind_england=R["hm"]["by_kind_england"],
           by_kind_midlands_north=R["hm"]["by_kind_midlands_north"], by_kind_scotland=R["hm"]["by_kind_scotland"]),
           top_uk=R["top_uk"][:25], regional_words_top=__import__("pandas").read_csv(os.path.join(ROOT, "data", "regional_words.csv")).head(150).to_dict("records"), terms_list=terms_list, cells10_keys=PT["cells10_keys"])
t = t.replace("/*R*/", json.dumps(emb, ensure_ascii=False, separators=(",", ":")))
assert "{{" not in t
open(os.path.join(ROOT, "index.html"), "w").write(t)
print("index.html", os.path.getsize(os.path.join(ROOT, "index.html")))
