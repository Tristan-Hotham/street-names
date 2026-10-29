"""Shared helpers for the static figures: fonts, palette, the UK outline and grid squares on the British National Grid."""
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection, PolyCollection
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    p = os.path.join(FONT_DIR, f)
    if os.path.exists(p): fm.fontManager.addfont(p)
DISP = fm.FontProperties(fname=os.path.join(FONT_DIR, "FrauncesVar.ttf"), weight=900) if os.path.exists(os.path.join(FONT_DIR, "FrauncesVar.ttf")) else fm.FontProperties(family="serif", weight="bold")
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, LAND, NONE = "#F6F3EC", "#16181D", "#5F6168", "#DCD6C9", "#E9E4D8", "#DDD7CB"
HIGH, MAIN = "#B5322B", "#1F4E8C"
HM = LinearSegmentedColormap.from_list("hm", [HIGH, "#E9E1EA", MAIN])
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
plt.rcParams.update({"font.family": SER, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT, "savefig.facecolor": BG, "figure.facecolor": BG, "axes.facecolor": BG})

_t = Transformer.from_crs(4326, 27700, always_xy=True)
def land_polys():
    g = json.load(open(os.path.join(ROOT, "data", "page", "land.json")))
    geoms = g["geometries"] if g["type"] == "GeometryCollection" else [g]
    polys = []
    for gg in geoms:
        if gg["type"] == "MultiPolygon": polys += gg["coordinates"]
        elif gg["type"] == "Polygon": polys.append(gg["coordinates"])
    out = []
    for p in polys:
        a = np.array(p[0]); x, y = _t.transform(a[:, 0], a[:, 1]); out.append(np.column_stack([x, y]))
    return out
LAND_P = None
def draw_land(ax, fc=LAND, ec="none", lw=0, z=0):
    global LAND_P
    if LAND_P is None: LAND_P = land_polys()
    ax.add_collection(PolyCollection(LAND_P, facecolors=fc, edgecolors=ec, linewidths=lw, zorder=z))
def frame(ax, x0=-20000, x1=660000, y0=0, y1=1000000):
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal"); ax.axis("off")
def cells(size):
    c = pd.read_pickle(os.path.join(ROOT, "work", "c10.pkl" if size == 10000 else "c20.pkl"))
    return c
def squares(ax, df, size, colours, z=2, ec="none", lw=0):
    rects = [Rectangle((cx * size, cy * size), size, size) for cx, cy in zip(df.cx, df.cy)]
    ax.add_collection(PatchCollection(rects, facecolors=colours, edgecolors=ec, linewidths=lw, zorder=z))
def streets():
    st = pd.read_pickle(os.path.join(ROOT, "work", "streets.pkl.gz"))
    for c in ["name", "generic", "first", "last", "lang", "lang2", "la_nation"]: st[c] = st[c].astype(str)
    return st
def label_cities(ax, names, fs=9, color=FG):
    pl = pd.read_pickle(os.path.join(ROOT, "work", "places.pkl"))
    for nm in names:
        r = pl[(pl.name == nm) & (pl.r >= 3)].head(1)
        if not len(r): continue
        x, y = _t.transform(r.lon.values[0], r.lat.values[0])
        ax.plot(x, y, "o", ms=2.6, color=color, zorder=6)
        ax.text(x + 7000, y, nm, family=MONO, fontsize=fs, color=color, va="center", zorder=6,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=2.2, foreground=BG)])
