"""Step 1: read the two raw bundles, make one table of UK named streets.

Inputs (read in place, paths at the top):
  OS Open Names (Great Britain), rows of LOCAL_TYPE "Named Road", reduced in the browser
  OpenStreetMap ways with highway and name in Northern Ireland (Overpass API)
  ONS local authority district boundaries (UK, 2025) from onsvisual/uk-topojson

Output: work/streets.pkl (one row per street), work/places.pkl (settlements for labels and search)
Run: python3 code/01_prepare.py
"""
import gzip, json, os, re, sys
import numpy as np, pandas as pd
from pyproj import Transformer
import shapely
from shapely.geometry import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("RAW_DIR", "/home/claude/hist/_data18/street-names")
LTLA = os.environ.get("LTLA", "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson")
OSN = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
WORK = os.path.join(ROOT, "work"); os.makedirs(WORK, exist_ok=True)
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)

# ---------- Great Britain: OS Open Names named roads ----------
g = json.load(gzip.open(os.path.join(RAW, "sn_osnames_roads_gb.json.gz")))
Dd, C = g["dicts"], g["cols"]
gb = pd.DataFrame({
    "name": np.array(Dd["name"], dtype=object)[C["n1"]],
    "lang": np.array(Dd["lang"], dtype=object)[C["l1"]],
    "name2": np.array(Dd["name"], dtype=object)[C["n2"]],
    "lang2": np.array(Dd["lang"], dtype=object)[C["l2"]],
    "x": np.array(C["x"], dtype=float), "y": np.array(C["y"], dtype=float),
    "ext": np.hypot(C["dx"], C["dy"]).astype(float),
    "place": np.array(Dd["pp"], dtype=object)[C["pp"]],
    "nation": np.array(Dd["ct"], dtype=object)[C["ct"]],
    "region": np.array(Dd["rg"], dtype=object)[C["rg"]],
})
gb["src"] = "OS"
print("GB named roads", len(gb), gb_retrieved := g["retrieved"])

# ---------- Northern Ireland: OSM ways clustered into streets ----------
n = json.load(gzip.open(os.path.join(RAW, "sn_osm_ni_roads.json.gz")))      # place nodes (and an earlier way list)
nw = json.load(gzip.open(os.path.join(RAW, "sn_osm_ni_ways_geom.json.gz")))  # ways with end nodes and length
ni = pd.DataFrame(nw["ways"], columns=nw["cols"])
ni_ways_all = len(n["roads"])          # every named highway way, any type
ni_ways_kept = len(ni)                 # road types only (no paths, tracks, service roads)
ni["x"], ni["y"] = to_bng.transform(ni.lon_mid.values, ni.lat_mid.values)
ni["xa"], ni["ya"] = to_bng.transform(ni.lon_a.values, ni.lat_a.values)
ni["xb"], ni["yb"] = to_bng.transform(ni.lon_b.values, ni.lat_b.values)
# OSM splits one street into many ways; OS Open Names has one feature per named road.
# Chain same-named ways that share an end node, or whose ends lie within LINK metres
# (gaps in mapping, the two halves of a dual carriageway).
LINK = 50.0
rows = []
for name, grp in ni.groupby("name"):
    m = len(grp); par = list(range(m))
    def find(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    ends = np.vstack([grp[["xa", "ya"]].values, grp[["xb", "yb"]].values]); idx = np.r_[np.arange(m), np.arange(m)]
    nodes = np.r_[grp.node_a.values, grp.node_b.values]
    if m > 1:
        d2 = ((ends[:, None, :] - ends[None, :, :]) ** 2).sum(-1)
        A, B = np.nonzero((d2 <= LINK ** 2) | (nodes[:, None] == nodes[None, :]))
        for a, b in zip(idx[A], idx[B]):
            ra, rb = find(a), find(b)
            if ra != rb: par[ra] = rb
    lab = np.array([find(i) for i in range(m)])
    for c in np.unique(lab):
        s = grp[lab == c]
        ga = s.name_ga[s.name_ga != ""]
        w = s.length_m.values.astype(float) + 1
        rows.append(dict(name=name, lang="", name2=(ga.iloc[0] if len(ga) else ""), lang2=("gle" if len(ga) else ""),
                         x=float(np.average(s.x, weights=w)), y=float(np.average(s.y, weights=w)), ext=float(s.length_m.sum()),
                         place="", nation="Northern Ireland", region="Northern Ireland", src="OSM"))
nis = pd.DataFrame(rows)
# OSM often names a bridge separately ("Queen's Bridge") on a short way inside a street; OS names roads, not bridges.
is_bridge = nis.name.str.endswith(" Bridge") & (nis.ext < 500)
ni_bridges_dropped = int(is_bridge.sum()); nis = nis[~is_bridge].reset_index(drop=True)
print("NI ways", ni_ways_all, "kept", ni_ways_kept, "streets", len(nis))

st = pd.concat([gb, nis], ignore_index=True)

# ---------- local authority by point in polygon (ONS 2025 boundaries) ----------
lj = json.load(open(LTLA))
polys, codes, names = [], [], []
for f in lj["features"]:
    if f["properties"].get("end") is not None: continue  # superseded districts carry an end year
    geom = shape(f["geometry"])
    geom = shapely.transform(geom, lambda a: np.column_stack(to_bng.transform(a[:, 0], a[:, 1])))
    polys.append(geom); codes.append(f["properties"]["areacd"]); names.append(f["properties"]["areanm"])
tree = shapely.STRtree(polys)
pts = shapely.points(st.x.values, st.y.values)
pi, gi = tree.query(pts, predicate="within")
la = np.full(len(st), -1); la[pi] = gi
miss = np.nonzero(la < 0)[0]
if len(miss):  # points just off the generalised coast: nearest polygon
    near = tree.query_nearest(pts[miss], return_distance=True)
    la[miss[near[0][0]]] = near[0][1]
    print("snapped to nearest council", len(miss), "max distance m", round(float(near[1].max())))
st["la_code"] = np.array(codes)[la]; st["la_name"] = np.array(names)[la]
st["la_nation"] = st.la_code.str[0].map({"E": "England", "W": "Wales", "S": "Scotland", "N": "Northern Ireland"})
mism = (st.la_nation != st.nation).sum()
print("nation disagreements OS vs ONS boundary", mism)
st["snap"] = False; st.loc[miss, "snap"] = True

# ---------- 10 km grid ----------
st["c10"] = (st.x // 10000).astype(int).astype(str) + "_" + (st.y // 10000).astype(int).astype(str)

# ---------- name parsing ----------
GENERICS = ["Street", "Road", "Lane", "Avenue", "Close", "Drive", "Way", "Gardens", "Crescent", "Court", "Place",
    "Terrace", "Grove", "View", "Walk", "Hill", "Row", "Park", "Mews", "Rise", "Green", "Square", "Mount", "Wynd",
    "Vennel", "Brae", "Loan", "Loke", "Twitten", "Ginnel", "Gennel", "Jennel", "Snicket", "Chare", "Gate", "Fold",
    "Brow", "Garth", "Bank", "Croft", "Drove", "Tye", "Chase", "Ope", "Yard", "Passage", "Alley", "Path", "Parade",
    "Meadow", "Meadows", "Field", "Fields", "Lea", "Leys", "Approach", "Boulevard", "Circle", "Circus", "End",
    "Glade", "Glen", "Hollow", "Nook", "Paddock", "Quay", "Reach", "Ride", "Side", "Spinney", "Steps", "Vale",
    "Villas", "Wharf", "Wood", "Woods", "Pend", "Entry", "Twitchel", "Twitchell", "Jitty", "Gully", "Coombe",
    "Combe", "Holme", "Dene", "Den", "Knowe", "Gait", "Causeway", "Highway", "Broadway", "Bridge", "Hey", "Heys",
    "Ley", "Oval", "Precinct", "Cottages", "Houses", "Buildings", "Estate", "Market", "Common", "Moor", "Heath",
    "Farm", "Lodge", "Copse", "Dell", "Down", "Downs", "Edge", "Orchard", "Pastures", "Plain", "Point", "Bottom",
    "Brook", "Cross", "Embankment", "Esplanade", "Promenade", "Front", "Rank", "Shaw", "Wells", "Yards"]
GEN = {w.lower() for w in GENERICS}
WELSH1 = {"heol", "ffordd", "stryd", "lôn", "lon", "rhodfa", "cilgant", "clos", "maes", "teras", "llwyn", "rhiw",
          "cwrt", "llys", "ael", "bryn", "pant", "cae", "tan", "penlan", "allt"}
GAEL1 = {"rathad", "sràid", "sraid", "ceum", "cnoc", "barraid", "ionad", "corran", "goirtean", "taobh", "sgìre"}
IRISH1 = {"bóthar", "sráid", "ascaill", "lána", "cnoc", "ardán", "páirc", "corrán", "plás", "céide", "slí", "bealach"}

def parse(nm):
    w = nm.split()
    if not w: return "", ""
    last = w[-1].lower().strip(".,'")
    if len(w) >= 2 and last in GEN:
        return " ".join(w[:-1]), w[-1].title()
    return nm, ""  # one-word names and names without an English generic word

sp = st.name.map(parse)
st["specific"] = [a for a, b in sp]; st["generic"] = [b for a, b in sp]
st["first"] = st.name.str.split().str[0].str.lower().fillna("")
st["last"] = st.name.str.split().str[-1].str.lower().fillna("")
st["one_word"] = ~st.name.str.contains(" ")
for col in ["name", "lang", "name2", "lang2", "place", "nation", "region", "src", "la_code", "la_name", "la_nation", "c10", "specific", "generic", "first", "last"]:
    st[col] = st[col].astype("category")
st.to_pickle(os.path.join(WORK, "streets.pkl.gz"), compression="gzip")

meta = dict(gb_retrieved=gb_retrieved, ni_retrieved=nw["retrieved"], ni_ways_all=ni_ways_all, ni_ways_kept=ni_ways_kept,
            ni_streets=len(nis), ni_bridges_dropped=ni_bridges_dropped, gb_streets=len(gb), link_m=LINK, snapped=int(len(miss)), nation_mismatch=int(mism))
json.dump(meta, open(os.path.join(WORK, "prep_meta.json"), "w"), indent=1)

# ---------- settlements for labels and search ----------
pl = pd.read_csv(OSN, sep="\t", usecols=["name1", "type", "local_type", "lat", "lon", "county"], dtype=str)
pl = pl[pl.type == "populatedPlace"].copy()
rank = {"City": 4, "Town": 3, "Village": 1, "Suburban Area": 1, "Hamlet": 0, "Other Settlement": 0}
pl["r"] = pl.local_type.map(rank); pl["lat"] = pl.lat.astype(float); pl["lon"] = pl.lon.astype(float)
pl = pl.rename(columns={"name1": "name", "local_type": "kind"})[["name", "kind", "county", "lat", "lon", "r"]]
npl = pd.DataFrame(n["places"], columns=n["places_cols"])
npl["r"] = npl.place.map({"city": 4, "town": 3, "village": 1, "suburb": 1, "hamlet": 0}); npl["county"] = "Northern Ireland"; npl["kind"] = npl.place.str.title()
pl = pd.concat([pl, npl[["name", "kind", "county", "lat", "lon", "r"]]], ignore_index=True)
pl.to_pickle(os.path.join(WORK, "places.pkl"))
print(json.dumps(meta))
