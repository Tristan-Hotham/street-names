"""Step 3: compact files for the interactive page (data/page/).

cells10.json, cells20.json : grid squares (corners in WGS84), street counts, top names, counts of every tracked term
councils.json              : simplified council boundaries (GeoJSON) with the same statistics
land.json                  : simplified UK outline (union of the councils), so the map reads without web tiles
places.json                : settlements for map labels and the place search
names/<letter>.json        : every street name and the 10 km squares where it occurs (for "find your street name")
Run: python3 code/03_page_data.py
"""
import json, os, re, unicodedata
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK, DATA = os.path.join(ROOT, "work"), os.path.join(ROOT, "data")
PAGE = os.path.join(DATA, "page"); os.makedirs(os.path.join(PAGE, "names"), exist_ok=True)
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
to_ll = Transformer.from_crs(27700, 4326, always_xy=True)
TL = json.load(open(os.path.join(WORK, "terms.json")))
TK = list(TL)
R = json.load(open(os.path.join(DATA, "results.json")))
st = pd.read_pickle(os.path.join(WORK, "streets.pkl.gz"))
st["name"] = st.name.astype(str); st["c10"] = st.c10.astype(str)

def dump(obj, name):
    p = os.path.join(PAGE, name)
    json.dump(obj, open(p, "w"), separators=(",", ":"), ensure_ascii=False)
    return os.path.getsize(p)

def corners(cx, cy, size):
    xs = np.array([cx, cx + 1, cx + 1, cx]) * size; ys = np.array([cy, cy, cy + 1, cy + 1]) * size
    lo, la = to_ll.transform(xs, ys)
    return [round(v, 4) for p in zip(la, lo) for v in p]

def sparse(row):
    out = []
    for j, k in enumerate(TK):
        v = int(row[k])
        if v: out += [j, v]
    return out

sizes = {}
for nm, size in [("cells10.json", 10000), ("cells20.json", 20000)]:
    c = pd.read_pickle(os.path.join(WORK, "c10.pkl" if size == 10000 else "c20.pkl"))
    rows = []
    for key, r in c.iterrows():
        rows.append([key, int(r.n), corners(int(r.cx), int(r.cy), size), r["top"], sparse(r), r.nation[0] if r.nation != "Northern Ireland" else "N"])
    sizes[nm] = dump(dict(size_km=size // 1000, rows=rows), nm)

# councils
lat = pd.read_csv(os.path.join(DATA, "councils.csv")).set_index("la_code")
top8 = st.groupby(["la_code", "name"], observed=True).size().rename("c").reset_index().sort_values(["la_code", "c"], ascending=[True, False]).groupby("la_code").head(8)
tops = {k: [[a, int(b)] for a, b in zip(g.name, g.c)] for k, g in top8.groupby("la_code")}
lj = json.load(open(LTLA)); feats = []; geoms = []
for f in lj["features"]:
    p = f["properties"]
    if p.get("end") is not None or p["areacd"] not in lat.index: continue
    g = shapely.make_valid(shape(f["geometry"])).simplify(0.004, preserve_topology=True)
    g = shapely.set_precision(g, 0.0001); geoms.append(g)
    r = lat.loc[p["areacd"]]
    row = {k: int(r["t_" + k]) for k in TK}
    feats.append(dict(type="Feature", geometry=mapping(g), properties=dict(
        c=p["areacd"], nm=p["areanm"], n=int(r.streets), top=tops.get(p["areacd"], []),
        sig=(None if pd.isna(r.signature) else [r.signature, int(r.signature_count), int(r.signature_uk)]),
        t=sparse(row))))
sizes["councils.json"] = dump(dict(type="FeatureCollection", features=feats), "councils.json")
land = shapely.union_all(geoms).simplify(0.006, preserve_topology=True)
land = shapely.set_precision(land, 0.0001)
sizes["land.json"] = dump(mapping(land), "land.json")

# places: labels (towns, cities, villages) and search
pl = pd.read_pickle(os.path.join(WORK, "places.pkl"))
pl = pl[pl.r >= 1].copy()
pl["county"] = pl.county.fillna("")
pl = pl.sort_values("r", ascending=False).drop_duplicates(["name", "county", "r"])
sizes["places.json"] = dump([[a, b, round(c, 4), round(d, 4), int(e)] for a, b, c, d, e in zip(pl.name, pl.county, pl.lat, pl.lon, pl.r)], "places.json")

# name shards
c10 = pd.read_pickle(os.path.join(WORK, "c10.pkl"))
cid = {k: j for j, k in enumerate(c10.index)}
def shard(nm):
    s = unicodedata.normalize("NFKD", nm.lower()); s = "".join(ch for ch in s if not unicodedata.combining(ch))
    ch = s[:1]
    return ch if "a" <= ch <= "z" else "_"
g = st.groupby(["name", "c10"], observed=True).size().rename("c").reset_index()
g["cell"] = g.c10.map(cid)
out = {}
for nm, grp in g.groupby("name", observed=True):
    out.setdefault(shard(nm), {})[nm] = [int(v) for pair in zip(grp.cell, grp.c) for v in pair]
tot = 0
for k, d in out.items(): tot += dump(d, f"names/{k}.json")
sizes["names/*"] = tot
sizes["names_shards"] = len(out)
json.dump(dict(terms=[dict(key=k, **TL[k]) for k in TK], cells10_keys=list(c10.index)), open(os.path.join(PAGE, "terms.json"), "w"), separators=(",", ":"), ensure_ascii=False)
sizes["terms.json"] = os.path.getsize(os.path.join(PAGE, "terms.json"))
print(sizes)

# reusable table: every street name with its count in each nation
nc = st.groupby(["name", "la_nation"], observed=True).size().unstack(fill_value=0)
nc = nc.reindex(columns=["England", "Scotland", "Wales", "Northern Ireland"], fill_value=0)
nc.insert(0, "uk", nc.sum(axis=1)); nc = nc.sort_values("uk", ascending=False)
nc.to_csv(os.path.join(DATA, "name_counts.csv.gz"), compression="gzip")
print("name_counts", len(nc), os.path.getsize(os.path.join(DATA, "name_counts.csv.gz")))
