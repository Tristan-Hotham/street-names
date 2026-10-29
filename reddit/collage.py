"""r/dataisbeautiful collage: High Street or Main Street? 2400 x 3000 px. Run: FONT_DIR=path/to/fonts python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"))
from figlib import *

BGC = "#F3EEE3"
plt.rcParams.update({"savefig.facecolor": BGC, "figure.facecolor": BGC, "axes.facecolor": BGC})
st = streets(); hm = R["hm"]
fig = plt.figure(figsize=(12, 15), dpi=200)

def sign(x, y, txt, fg, bg, ed, fs):
    fig.text(x, y, txt, fontproperties=DISP, fontsize=fs, color=fg, va="center",
             bbox=dict(boxstyle="round,pad=0.32,rounding_size=0.3", fc=bg, ec=ed, lw=4))
sign(.05, .953, "HIGH STREET", "#111", "#fff", "#111", 37)
fig.text(.465, .953, "or", family=SER, style="italic", fontsize=34, color=FG, va="center")
sign(.53, .953, "MAIN STREET?", "#fff", MAIN, "#fff", 37)
fig.text(.045, .912, f"All {R['meta']['n_streets']:,} named streets in the UK, sorted by name. Where High Street gives way to\nMain Street, and the street words that belong to one corner of the country.",
         family=SER, fontsize=15.5, color=FG, va="top", linespacing=1.4)

# hero map
c = cells(20000); h, m = c.high_street, c.main_street; has = (h + m) > 0
ax = fig.add_axes([.0, .325, .60, .535]); draw_land(ax)
squares(ax, c[~has], 20000, NONE, z=1)
squares(ax, c[has], 20000, [HM(v) for v in (m / (h + m))[has]], z=2, ec=BGC, lw=.5)
frame(ax, -10000, 670000, 0, 990000)
label_cities(ax, ["London", "Leeds", "Nottingham", "Edinburgh", "Belfast", "Cardiff", "Norwich", "Glasgow"], fs=10)
lx = fig.add_axes([.62, .345, .26, .012]); lx.imshow(np.linspace(0, 1, 256)[None, :], cmap=HM, aspect="auto"); lx.set_xticks([0, 255]); lx.set_xticklabels(["all High", "all Main"], family=MONO, fontsize=10); lx.set_yticks([])
[sp.set_visible(False) for sp in lx.spines.values()]
fig.text(.62, .363, "Main Street's share of each\n20 km square's High + Main", family=MONO, fontsize=10, color=FG, va="bottom")

# big numbers
tx = fig.add_axes([.60, .40, .37, .46]); tx.axis("off")
items = [
 (f"{hm['uk']['high']:,} : {hm['uk']['main']:,}", "High Streets to Main Streets in the UK.\nHigh Street is the commonest name of all."),
 (f"{round(hm['by_kind_midlands_north']['Village']['main_share']*100)}% vs {round(hm['by_kind_midlands_north']['Town']['main_share']*100)}%", "Main Street's share in East Midlands and\nYorkshire villages vs their towns.\nMain Street is a village name."),
 (f"{hm['region']['East Midlands']['main']} : {hm['region']['East Midlands']['high']}", "Main to High Streets in the East Midlands.\nThe North East, next to Scotland,\nhas just " + str(hm['region']['North East']['main']) + " Main Streets."),
 (f"{hm['nation']['Scotland']['main']} : {hm['nation']['Scotland']['high']}", f"Main to High in Scotland; Northern Ireland\n{hm['nation']['Northern Ireland']['main']} : {hm['nation']['Northern Ireland']['high']}. London: {hm['region']['London']['high']} High, 1 Main."),
]
y = .97
for big, small in items:
    col = MAIN if big.startswith(("6", "4", "3")) and ":" in big and big[0] in "43" else (HIGH if big.startswith("2") else MAIN)
    tx.text(0, y, big, fontproperties=DISP, fontsize=33, color=col, va="top", transform=tx.transAxes)
    tx.text(0, y - .095, small, family=SER, fontsize=12.5, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)
    y -= .255

# small multiples
WORDS = [("The Street", st.name == "The Street", "#C27C0E", "East and SE"), ("Fore Street", st.name == "Fore Street", "#1E9AA0", "South West"),
         ("Front Street", st.name == "Front Street", "#6B4BA0", "North East"), ("Wynd", st.generic == "Wynd", MAIN, "Scotland"),
         ("Garth", st.generic == "Garth", "#6B4BA0", "Yorkshire"), ("Loke", st.generic == "Loke", "#C27C0E", "Norfolk")]
fig.text(.045, .308, "OTHER MAIN STREETS AND REGIONAL STREET WORDS  (each dot is a street)", family=MONO, fontsize=11, color=MUT)
for j, (lab, msk, col, where) in enumerate(WORDS):
    a = fig.add_axes([.01 + j * .165, .07, .165, .19]); draw_land(a)
    mm = msk.values; a.scatter(st.x.values[mm], st.y.values[mm], s=3.2, color=col, lw=0, alpha=.85, zorder=3)
    frame(a, 0, 660000, 0, 980000)
    a.set_title(f"{lab}\n{int(mm.sum()):,}, {where}", family=MONO, fontsize=10.5, color=FG, pad=1, linespacing=1.3)

fig.text(.045, .022, "Data: OS Open Names (Named Road), contains OS data © Crown copyright and database right 2026 (OGL v3); Northern Ireland from\n© OpenStreetMap contributors (ODbL). Exact names only. Interactive: maps.tristanhotham.com/street-names\nAnalysis and chart: Tristan Hotham, with Python and matplotlib.",
         family=MONO, fontsize=9, color=MUT, linespacing=1.45)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "high_street_main_street.png")
fig.savefig(out, dpi=200); print(out)
