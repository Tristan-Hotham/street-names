"""Step 5: static figures for the blog and paper (release/blog/b_*.png, 1520 px wide) and the social card header.png.
Run: FONT_DIR=path/to/fonts python3 code/05_figures.py
"""
import os, json
import numpy as np, pandas as pd
from figlib import *
import matplotlib.patheffects as pe

OUT = os.path.join(ROOT, "release", "blog"); os.makedirs(OUT, exist_ok=True)
DPI = 150; W = 1520 / DPI
st = streets()
TERMS = json.load(open(os.path.join(ROOT, "work", "terms.json")))

def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=DPI); plt.close(fig); print(name)

def hm_map(ax, size=20000, cities=True):
    c = cells(size)
    draw_land(ax)
    h, m = c.high_street, c.main_street
    has = (h + m) > 0
    squares(ax, c[~has], size, NONE, z=1)
    squares(ax, c[has], size, [HM(v) for v in (m / (h + m))[has]], z=2, ec=BG, lw=.35)
    frame(ax, -10000, 670000, -5000, 1000000)
    if cities: label_cities(ax, ["London", "Birmingham", "Leeds", "Nottingham", "Leicester", "Norwich", "Glasgow", "Edinburgh", "Aberdeen", "Inverness", "Belfast", "Cardiff", "Plymouth", "York", "Newcastle upon Tyne"], fs=9.5)

# 1. the divide map
fig = plt.figure(figsize=(W, W * 1.18))
ax = fig.add_axes([0, 0, .74, 1]); hm_map(ax)
lx = fig.add_axes([.70, .62, .26, .028])
lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=HM, aspect="auto"); lx.set_xticks([0, 127, 255]); lx.set_xticklabels(["all High", "half", "all Main"], family=MONO, fontsize=11); lx.set_yticks([])
for s in lx.spines.values(): s.set_visible(False)
fig.text(.70, .665, "Main Street's share of\neach 20 km square's\nHigh and Main Streets", family=MONO, fontsize=12, color=FG, va="bottom")
fig.text(.70, .575, "grey: neither name", family=MONO, fontsize=11, color=MUT)
save(fig, "b_divide_map.png")

# 2. regions
reg = sorted(R["hm"]["region"].items(), key=lambda kv: kv[1]["main_share"])
fig, ax = plt.subplots(figsize=(W, 6.2)); fig.subplots_adjust(left=.27, right=.9, top=.97, bottom=.1)
for j, (k, v) in enumerate(reg):
    ax.barh(j, v["main_share"], color=HM(v["main_share"]), height=.72)
    ax.text(v["main_share"] + .012, j, f"{v['main_share']*100:.0f}%   {v['main']} of {v['high']+v['main']}", va="center", family=MONO, fontsize=12, color=FG)
ax.set_yticks(range(len(reg))); ax.set_yticklabels([("East of England" if k == "Eastern" else k) for k, _ in reg], fontsize=14)
ax.set_xlim(0, 1); ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], family=MONO, fontsize=12)
ax.axvline(.5, color=MUT, lw=.8, ls=":"); [ax.spines[s].set_visible(False) for s in ["top", "right", "left"]]; ax.tick_params(left=False)
save(fig, "b_regions.png")

# 3. towns and villages
groups = [("England", R["hm"]["by_kind_england"]), ("East Midlands and Yorkshire", R["hm"]["by_kind_midlands_north"]), ("Scotland", R["hm"]["by_kind_scotland"])]
fig, ax = plt.subplots(figsize=(W, 4.6)); fig.subplots_adjust(left=.37, right=.93, top=.95, bottom=.14)
y = 0; yt, yl = [], []
for lab, d in groups[::-1]:
    for k in ["Village", "Town"]:
        v = d[k]; ax.barh(y, v["main_share"], color=HM(v["main_share"]), height=.75)
        ax.text(v["main_share"] + .012, y, f"{v['main_share']*100:.0f}%  ({v['high']+v['main']:,})", va="center", family=MONO, fontsize=12)
        yt.append(y); yl.append(f"{lab}, {'villages' if k == 'Village' else 'towns'}"); y += 1
    y += .6
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=13.5); ax.set_xlim(0, 1)
ax.set_xticks([0, .25, .5, .75, 1]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], family=MONO, fontsize=12)
ax.set_xlabel("Main Street's share of High plus Main Streets", family=MONO, fontsize=12, color=MUT)
[ax.spines[s].set_visible(False) for s in ["top", "right", "left"]]; ax.tick_params(left=False)
save(fig, "b_towns_villages.png")

# 4. the five main-street words, 20 km
c = cells(20000); fw = ["high_street", "main_street", "the_street", "fore_street", "front_street"]
FWC = {"high_street": HIGH, "main_street": MAIN, "the_street": "#D08A12", "fore_street": "#1E9AA0", "front_street": "#6B4BA0"}
FWL = {"high_street": "High Street", "main_street": "Main Street", "the_street": "The Street", "fore_street": "Fore Street", "front_street": "Front Street"}
sub = c[c[fw].sum(axis=1) >= 3]; win = sub[fw].idxmax(axis=1)
fig = plt.figure(figsize=(W, W * 1.18)); ax = fig.add_axes([0, 0, .74, 1]); draw_land(ax)
squares(ax, c[~c.index.isin(sub.index)], 20000, NONE, z=1)
squares(ax, sub, 20000, [FWC[w] for w in win], z=2, ec=BG, lw=.35); frame(ax, -10000, 670000, -5000, 1000000)
for j, k in enumerate(fw):
    fig.text(.71, .7 - j * .04, "■", color=FWC[k], fontsize=22, va="center")
    fig.text(.745, .7 - j * .04, f"{FWL[k]}  {R['cells']['main_word_20km'][k]}", family=MONO, fontsize=13, va="center")
fig.text(.71, .75, "Commonest of the five\nnames for the main street,\n20 km squares with 3+", family=MONO, fontsize=12, color=FG, va="bottom")
save(fig, "b_main_words.png")

# 5. regional words small multiples, street points
WORDS = [("r_wynd", "Wynd"), ("r_brae", "Brae"), ("r_chare", "Chare"), ("r_garth", "Garth"), ("r_brow", "Brow"), ("r_fold", "Fold"), ("r_loke", "Loke"), ("r_drove", "Drove"), ("cy_heol", "Heol")]
def term_mask(k):
    gen, first, last, one = st.generic, st["first"], st["last"], ~st.name.str.contains(" ")
    return {"r_wynd": gen == "Wynd", "r_brae": gen == "Brae", "r_chare": gen == "Chare", "r_garth": gen == "Garth", "r_brow": gen == "Brow",
            "r_fold": gen == "Fold", "r_loke": gen == "Loke", "r_drove": gen == "Drove", "cy_heol": first == "heol",
            "the_street": st.name == "The Street", "fore_street": st.name == "Fore Street", "front_street": st.name == "Front Street", "r_loan": gen == "Loan"}[k]
COLS = ["#1F4E8C", "#1F4E8C", "#6B4BA0", "#6B4BA0", "#6B4BA0", "#6B4BA0", "#C27C0E", "#C27C0E", "#2E7D5B"]
fig, axs = plt.subplots(3, 3, figsize=(W, W * 1.25)); fig.subplots_adjust(left=.01, right=.99, top=.96, bottom=.01, wspace=.02, hspace=.12)
for a, (k, lab), col in zip(axs.flat, WORDS, COLS):
    draw_land(a); m = term_mask(k).values
    a.scatter(st.x.values[m], st.y.values[m], s=4, color=col, alpha=.8, lw=0, zorder=3); frame(a, -10000, 670000, -5000, 1000000)
    a.set_title(f"{lab}  {int(m.sum()):,}", family=MONO, fontsize=14, color=FG, pad=2)
save(fig, "b_regional_words.png")

# 6. top names
rows = R["top_uk"][:20]
fig, ax = plt.subplots(figsize=(W, 7.4)); fig.subplots_adjust(left=.2, right=.95, top=.98, bottom=.04)
for j, (n, cnt) in enumerate(rows):
    col = HIGH if n == "High Street" else MAIN if n == "Main Street" else "#8F9198"
    ax.barh(j, cnt, color=col, height=.72); ax.text(cnt + 20, j, f"{cnt:,}", va="center", family=MONO, fontsize=12)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([n for n, _ in rows], fontsize=13.5); ax.invert_yaxis(); ax.set_xticks([])
[ax.spines[s].set_visible(False) for s in ["top", "right", "left", "bottom"]]; ax.tick_params(left=False)
save(fig, "b_top_names.png")

# header.png 1200x630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([.60, .0, .40, 1]); hm_map(ax, cities=False); frame(ax, 0, 660000, 0, 980000)
def sign(x, y, txt, fg, bg, ed, fs=34):
    fig.text(x, y, txt, fontproperties=DISP, fontsize=fs, color=fg, va="center",
             bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.25", fc=bg, ec=ed, lw=3))
fig.text(.05, .9, "DATA STUDY  ·  UNITED KINGDOM", family=MONO, fontsize=13, color=MUT)
sign(.05, .74, "HIGH STREET", "#111", "#fff", "#111")
sign(.05, .56, "MAIN STREET", "#fff", MAIN, "#fff")
fig.text(.05, .40, f"{R['hm']['uk']['high']:,} High Streets, {R['hm']['uk']['main']:,} Main Streets.", family=SER, fontsize=20, color=FG)
fig.text(.05, .33, f"Where the UK's {R['meta']['n_streets']:,} street names change,", family=SER, fontsize=20, color=FG)
fig.text(.05, .26, "from Wynd to Loke, Garth and Chare.", family=SER, fontsize=20, color=FG)
fig.text(.05, .08, "Dr Tristan Hotham  ·  maps.tristanhotham.com/street-names", family=MONO, fontsize=12, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100); plt.close(fig); print("header.png")
