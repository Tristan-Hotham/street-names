"""Step 6: fill code/paper_template.tex from data/results.json and compile with xelatex.
Writes release/paper/ (tex and figures) and release/Hotham_High_Street_or_Main_Street.pdf. Run: python3 code/06_paper.py
"""
import json, os, re, shutil, subprocess
import pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RP = os.path.join(ROOT, "data", "results.json"); R = json.load(open(RP))
R["page"]["ni_before_bridges"] = R["meta"]["prep"]["ni_streets"] + R["meta"]["prep"]["ni_bridges_dropped"]
json.dump(R, open(RP, "w"), indent=1, ensure_ascii=False)
OUT = os.path.join(ROOT, "release", "paper"); os.makedirs(OUT, exist_ok=True)
NAME = "Hotham_High_Street_or_Main_Street"
def tex(s): return str(s).replace("&", r"\&").replace("%", r"\%").replace("_", r"\_").replace("#", r"\#")
def get(path):
    cur = R
    for k in path.split("."):
        cur = cur[int(k)] if isinstance(cur, list) else cur[k]
    return cur
def sub(m):
    path, _, fm = m.group(1).partition("|"); v = get(path.strip())
    if fm == "int": return f"{round(v):,}"
    if fm == "pct": return f"{round(v * 100)}\\%"
    if fm == "pct1": return f"{v * 100:.1f}\\%"
    if fm == "f1": return f"{v:.1f}"
    return tex(v)
nat = ["England", "Scotland", "Wales", "Northern Ireland"]
rows = [r"\begin{tabular}{rllll}", r"\toprule", r" & UK & England & Scotland & Wales and Northern Ireland \\", r"\midrule"]
for i in range(10):
    u = R["top_uk"][i]; e = R["top_nation"]["England"][i]; s = R["top_nation"]["Scotland"][i]; w = R["top_nation"]["Wales"][i]; n_ = R["top_nation"]["Northern Ireland"][i]
    rows.append(f"{i+1} & {tex(u[0])} ({u[1]:,}) & {tex(e[0])} ({e[1]:,}) & {tex(s[0])} ({s[1]:,}) & W: {tex(w[0])} ({w[1]:,}); NI: {tex(n_[0])} ({n_[1]:,}) \\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
tab_top = "\n".join(rows).replace("(", "(").replace("{tabular}{rllll}", "{tabular}{rp{3.1cm}p{3.1cm}p{3.1cm}p{4.2cm}}")
rows = [r"\begin{tabular}{lrrrr}", r"\toprule", r"Nation & Streets & High Street & Main Street & Main share \\", r"\midrule"]
for n_ in nat:
    h = R["hm"]["nation"][n_]; rows.append(f"{n_} & {R['meta']['by_nation'][n_]:,} & {h['high']:,} & {h['main']:,} & {round(h['main_share']*100)}\\% \\\\")
h = R["hm"]["uk"]; rows += [r"\midrule", f"UK & {R['meta']['n_streets']:,} & {h['high']:,} & {h['main']:,} & {round(h['main_share']*100)}\\% \\\\", r"\bottomrule", r"\end{tabular}"]
tab_hm = "\n".join(rows)
rw = pd.read_csv(os.path.join(ROOT, "data", "regional_words.csv")); rw = rw[rw.lq >= 3].groupby("region").head(3).head(20)
rows = [r"\begin{tabular}{llrlr}", r"\toprule", r"Word & Position & Streets & Top region (share there) & LQ \\", r"\midrule"]
for r in rw.itertuples():
    reg = "East of England" if r.region == "Eastern" else r.region
    rows.append(f"{tex(r.word)} & {r.kind} & {r.n:,} & {tex(reg)} ({round(r.share*100)}\\%) & {r.lq:.1f} \\\\")
rows += [r"\bottomrule", r"\end{tabular}"]
tab_rw = "\n".join(rows)
t = open(os.path.join(ROOT, "code", "paper_template.tex")).read()
t = t.replace("{{tab_top}}", tab_top).replace("{{tab_hm}}", tab_hm).replace("{{tab_rw}}", tab_rw)
t = re.sub(r"\{\{([^}]+)\}\}", sub, t)
assert "{{" not in t
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for f in ["b_divide_map.png", "b_regions.png", "b_towns_villages.png", "b_main_words.png", "b_regional_words.png"]:
    shutil.copy(os.path.join(ROOT, "release", "blog", f), os.path.join(OUT, f))
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
for ext in [".aux", ".log", ".out", ".pdf"]:
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
print("ok")
