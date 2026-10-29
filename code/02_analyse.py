"""Step 2: every statistic. Writes data/results.json and the reusable CSV tables in data/.

Run: python3 code/02_analyse.py   (after 01_prepare.py)
"""
import json, os, re
import numpy as np, pandas as pd
from pyproj import Transformer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK, DATA = os.path.join(ROOT, "work"), os.path.join(ROOT, "data")
os.makedirs(DATA, exist_ok=True)
st = pd.read_pickle(os.path.join(WORK, "streets.pkl.gz"))
for col in st.columns:
    if isinstance(st[col].dtype, pd.CategoricalDtype): st[col] = st[col].astype(object)
pl = pd.read_pickle(os.path.join(WORK, "places.pkl"))
prep = json.load(open(os.path.join(WORK, "prep_meta.json")))
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland"]
st["nat"] = st.la_nation
st["reg"] = np.where(st.nat == "England", st.region, st.nat)
# OS region for England comes from OS Open Names; 23 points sit across a national border from their OS nation: use ONS.
st.loc[(st.nat == "England") & ~st.region.isin(["London", "South East", "South West", "Eastern", "East Midlands", "West Midlands",
        "North West", "North East", "Yorkshire and the Humber"]), "reg"] = np.nan
modal = st[st.reg.notna()].groupby("la_code").reg.agg(lambda s: s.value_counts().index[0])
st["reg"] = st.reg.fillna(st.la_code.map(modal))
R = {}

def i(x): return int(x)
def r3(x): return round(float(x), 4)

# ---------------- term definitions ----------------
low = st.name.str.lower()
spec = st.specific.str.lower()
gen = st.generic
first = st["first"]; last = st["last"]; one = st.one_word
words = low.str.replace(r"[^a-zà-ÿâêîôûŵŷ' ]", " ", regex=True).str.split()
wset = words.map(set)
def has_word(*ws):
    ws = set(ws); return wset.map(lambda s: bool(s & ws))
def exact(nm): return st.name == nm

TERMS = [  # key, label, group, mask, note
 ("high_street", "High Street", "name", exact("High Street"), ""),
 ("main_street", "Main Street", "name", exact("Main Street"), ""),
 ("the_street", "The Street", "name", exact("The Street"), ""),
 ("fore_street", "Fore Street", "name", exact("Fore Street"), ""),
 ("front_street", "Front Street", "name", exact("Front Street"), ""),
 ("station_road", "Station Road", "name", exact("Station Road"), ""),
 ("church_lane", "Church Lane", "name", exact("Church Lane"), ""),
 ("church_street", "Church Street", "name", exact("Church Street"), ""),
 ("mill_lane", "Mill Lane", "name", exact("Mill Lane"), ""),
 ("back_lane", "Back Lane", "name", exact("Back Lane"), ""),
 ("green_lane", "Green Lane", "name", exact("Green Lane"), ""),
 ("manse_road", "Manse Road", "name", exact("Manse Road"), ""),
 ("london_road", "London Road", "name", exact("London Road"), ""),
 ("belfast_road", "Belfast Road", "name", exact("Belfast Road"), ""),
 ("w_church", "Church", "word", has_word("church", "church's", "churchyard"), "any street with the word Church"),
 ("w_kirk", "Kirk", "word", has_word("kirk", "kirkgate") | first.str.startswith("kirk"), "Kirk as a word or at the start of the name"),
 ("w_chapel", "Chapel", "word", has_word("chapel"), ""),
 ("w_mill", "Mill", "word", has_word("mill", "mills"), ""),
 ("w_station", "Station", "word", has_word("station"), ""),
 ("w_school", "School", "word", has_word("school"), ""),
 ("w_back", "Back", "word", first == "back", "names starting with Back"),
 ("w_victoria", "Victoria", "royal", has_word("victoria"), ""),
 ("w_albert", "Albert", "royal", has_word("albert"), ""),
 ("w_queen", "Queen or Queen's", "royal", has_word("queen", "queen's", "queens"), ""),
 ("w_king", "King or King's", "royal", has_word("king", "king's", "kings"), ""),
 ("w_george", "George", "royal", has_word("george"), ""),
 ("w_elizabeth", "Elizabeth", "royal", has_word("elizabeth"), ""),
 ("w_coronation", "Coronation", "royal", has_word("coronation"), ""),
 ("w_jubilee", "Jubilee", "royal", has_word("jubilee"), ""),
 ("g_street", "... Street", "ending", gen == "Street", ""),
 ("g_road", "... Road", "ending", gen == "Road", ""),
 ("g_lane", "... Lane", "ending", gen == "Lane", ""),
 ("g_close", "... Close", "ending", gen == "Close", ""),
 ("g_avenue", "... Avenue", "ending", gen == "Avenue", ""),
 ("g_drive", "... Drive", "ending", gen == "Drive", ""),
 ("g_way", "... Way", "ending", gen == "Way", ""),
 ("g_gardens", "... Gardens", "ending", gen == "Gardens", ""),
 ("g_crescent", "... Crescent", "ending", gen == "Crescent", ""),
 ("g_terrace", "... Terrace", "ending", gen == "Terrace", ""),
 ("g_park", "... Park", "ending", gen == "Park", ""),
 ("g_mews", "... Mews", "ending", gen == "Mews", ""),
 ("g_row", "... Row", "ending", gen == "Row", ""),
 ("r_wynd", "Wynd", "regional", gen == "Wynd", ""),
 ("r_vennel", "Vennel", "regional", gen == "Vennel", ""),
 ("r_brae", "Brae", "regional", gen == "Brae", ""),
 ("r_loan", "Loan", "regional", gen == "Loan", ""),
 ("r_gait", "Gait", "regional", gen == "Gait", ""),
 ("r_pend", "Pend", "regional", gen == "Pend", ""),
 ("r_chare", "Chare", "regional", gen == "Chare", ""),
 ("r_gate", "-gate (one word) or ... Gate", "regional", (gen == "Gate") | (one & last.str.endswith("gate") & (last.str.len() > 5)), "e.g. Briggate, Kirkgate, Castle Gate"),
 ("r_garth", "Garth", "regional", gen == "Garth", ""),
 ("r_fold", "Fold", "regional", gen == "Fold", ""),
 ("r_brow", "Brow", "regional", gen == "Brow", ""),
 ("r_hey", "Hey", "regional", gen == "Hey", ""),
 ("r_croft", "Croft", "regional", gen == "Croft", ""),
 ("r_carr", "Carr", "regional", first == "carr", "names starting with Carr"),
 ("r_ings", "Ings", "regional", first == "ings", "names starting with Ings"),
 ("r_ginnel", "Ginnel, Gennel or Jennel", "regional", gen.isin(["Ginnel", "Gennel", "Jennel"]), ""),
 ("r_snicket", "Snicket", "regional", gen == "Snicket", ""),
 ("r_twitten", "Twitten", "regional", gen == "Twitten", ""),
 ("r_loke", "Loke", "regional", gen == "Loke", ""),
 ("r_drove", "Drove", "regional", gen == "Drove", ""),
 ("r_chase", "Chase", "regional", gen == "Chase", ""),
 ("r_tye", "Tye", "regional", gen == "Tye", ""),
 ("r_ope", "Ope", "regional", gen == "Ope", ""),
 ("r_combe", "Coombe or Combe", "regional", gen.isin(["Coombe", "Combe"]), ""),
 ("r_twitchel", "Twitchell or Jitty", "regional", gen.isin(["Twitchel", "Twitchell", "Jitty"]), ""),
 ("r_entry", "Entry", "regional", gen == "Entry", ""),
 ("cy_heol", "Heol", "welsh", first == "heol", "Welsh: road"),
 ("cy_ffordd", "Ffordd", "welsh", first == "ffordd", "Welsh: way, road"),
 ("cy_stryd", "Stryd", "welsh", first == "stryd", "Welsh: street"),
 ("cy_lon", "Lôn", "welsh", first.isin(["lôn", "lon"]), "Welsh: lane"),
 ("cy_clos", "Clos", "welsh", first == "clos", "Welsh: close"),
 ("cy_maes", "Maes", "welsh", first == "maes", "Welsh: field, square"),
 ("cy_llys", "Llys", "welsh", first == "llys", "Welsh: court"),
 ("cy_bryn", "Bryn", "welsh", first == "bryn", "Welsh: hill"),
 ("gd_rathad", "Rathad", "gaelic", has_word("rathad"), "Scottish Gaelic: road"),
]
# A Welsh street word at the start, in either the main name or the second-language name
WELSH_FIRST = {"heol", "ffordd", "stryd", "lôn", "lon", "clos", "maes", "llys", "cwrt", "rhodfa", "cilgant", "teras", "cae", "bryn", "llwyn", "rhes", "ffordd-y", "y"}
f2 = st.name2.str.split().str[0].str.lower().fillna("")
welsh_any = first.isin(WELSH_FIRST) | (st.lang == "cym") | (st.lang2 == "cym")
TERMS += [("cy_any", "Any Welsh name", "welsh", welsh_any & (st.nat == "Wales") | (st.lang == "cym") | (st.lang2 == "cym"),
           "Welsh as the main or second name in OS Open Names, or a Welsh street word first (in Wales)"),
          ("gd_any", "Any Gaelic name", "gaelic", (st.lang == "gla") | (st.lang2 == "gla"), "a Scottish Gaelic name in OS Open Names"),
          ("ga_any", "Irish name in OSM", "gaelic", (st.lang2 == "gle"), "Northern Ireland streets with an Irish name (name:ga) in OpenStreetMap")]
TM = {k: m.values.astype(bool) for k, lab, g, m, note in TERMS}
TL = {k: dict(label=lab, group=g, note=note) for k, lab, g, m, note in TERMS}

# ---------------- totals ----------------
R["meta"] = dict(n_streets=i(len(st)), n_gb=i((st.src == "OS").sum()), n_ni=i((st.src == "OSM").sum()),
    by_nation={n: i((st.nat == n).sum()) for n in NATIONS}, n_names=i(st.name.nunique()),
    n_councils=i(st.la_code.nunique()), prep=prep, n_cells10=i(st.c10.nunique()))
R["meta"]["unique_share"] = r3((st.name.value_counts() == 1).sum() / st.name.nunique())
R["meta"]["streets_with_unique_name"] = i((st.name.map(st.name.value_counts()) == 1).sum())

def top(df, k=20):
    vc = df.name.value_counts().head(k); return [[n, i(c)] for n, c in vc.items()]
R["top_uk"] = top(st, 40)
R["top_nation"] = {n: top(st[st.nat == n], 15) for n in NATIONS}
R["top_generic"] = [[g, i(c), r3(c / len(st))] for g, c in st[st.generic != ""].generic.value_counts().head(25).items()]
R["no_generic_share"] = r3((st.generic == "").mean())
R["generic_by_nation"] = {n: {g: r3(((st.nat == n) & (st.generic == g)).sum() / (st.nat == n).sum()) for g in
                          ["Road", "Close", "Street", "Lane", "Avenue", "Drive", "Way", "Court", "Place", "Gardens", "Crescent", "Park", "Terrace", "Wynd", "Brae"]} for n in NATIONS}

# ---------------- High Street v Main Street ----------------
H, M = TM["high_street"], TM["main_street"]
def hm(mask):
    h, m = i((H & mask).sum()), i((M & mask).sum()); return dict(high=h, main=m, main_share=(r3(m / (h + m)) if h + m else None))
R["hm"] = dict(uk=hm(np.ones(len(st), bool)), nation={n: hm((st.nat == n).values) for n in NATIONS},
               region={g: hm((st.reg == g).values) for g in sorted(st.reg.unique()) })
# by 50 km northing band, Great Britain (OS) only
b = (st.y // 50000).astype(int)
bands = []
for k in sorted(b[st.src == "OS"].unique()):
    msk = ((b == k) & (st.src == "OS")).values; d = hm(msk); d["y0_km"] = i(k * 50); bands.append(d)
R["hm"]["bands_gb"] = bands
# councils
la = st.groupby(["la_code", "la_name", "nat"]).size().rename("n").reset_index()
la["high"] = la.la_code.map(pd.Series(H, index=st.index).groupby(st.la_code).sum())
la["main"] = la.la_code.map(pd.Series(M, index=st.index).groupby(st.la_code).sum())
eng = la[la.nat == "England"]
R["hm"]["england_councils_main_more"] = i((eng.main > eng.high).sum())
R["hm"]["england_councils"] = i(len(eng))
R["hm"]["england_main_top"] = [[r.la_name, i(r.main), i(r.high)] for r in eng.sort_values(["main", "high"], ascending=[False, True]).head(12).itertuples()]
sco = la[la.nat == "Scotland"]
R["hm"]["scotland_high_more"] = [[r.la_name, i(r.high), i(r.main)] for r in sco[sco.high > sco.main].sort_values("high", ascending=False).itertuples()]
R["hm"]["scotland_councils"] = i(len(sco))
# settlement type: the street's OS populated place, matched by name to the nearest OS settlement of that name
to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
pl["x"], pl["y"] = to_bng.transform(pl.lon.values, pl.lat.values)
kind = pd.Series("", index=st.index, dtype=object)
gbp = pl[pl.county != "Northern Ireland"]
cand = {k: g for k, g in gbp.groupby("name")}
for pname, grp in st[(st.src == "OS") & (st.place != "")].groupby("place"):
    c = cand.get(pname)
    if c is None: continue
    d = (grp.x.values[:, None] - c.x.values[None, :]) ** 2 + (grp.y.values[:, None] - c.y.values[None, :]) ** 2
    j = d.argmin(1); ok = d[np.arange(len(j)), j] < 8000 ** 2
    kind.loc[grp.index[ok]] = c.kind.values[j[ok]]
st["kind"] = kind
R["hm"]["kind_matched_share"] = r3((st.kind[st.src == "OS"] != "").mean())
def kindgrp(k): return {"City": "City", "Town": "Town", "Suburban Area": "Suburb", "Village": "Village", "Hamlet": "Hamlet or other", "Other Settlement": "Hamlet or other"}.get(k, "")
st["kg"] = st.kind.map(kindgrp)
R["hm"]["by_kind_england"] = {k: hm(((st.kg == k) & (st.nat == "England")).values) for k in ["City", "Town", "Village", "Hamlet or other"]}
R["hm"]["by_kind_midlands_north"] = {k: hm(((st.kg == k) & st.reg.isin(["East Midlands", "Yorkshire and the Humber"])).values) for k in ["City", "Town", "Village", "Hamlet or other"]}
R["hm"]["by_kind_scotland"] = {k: hm(((st.kg == k) & (st.nat == "Scotland")).values) for k in ["City", "Town", "Village", "Hamlet or other"]}
# The Street, Fore Street, Front Street: the other words for the main street
R["main_words"] = {}
for k in ["high_street", "main_street", "the_street", "fore_street", "front_street"]:
    m = TM[k]; reg = pd.Series(m).groupby(st.reg.values).sum().sort_values(ascending=False)
    R["main_words"][k] = dict(n=i(m.sum()), top_regions=[[g, i(c), r3(c / m.sum())] for g, c in reg.head(3).items()])
# main street term per cell: which of the five is most common
# ---------------- terms: counts, regions, councils, concentration ----------------
Nreg = st.groupby("reg").size(); shreg = Nreg / Nreg.sum()
Nla = st.groupby("la_code").size(); lanm = st.groupby("la_code").la_name.first()
terms_out = {}
for k, meta in TL.items():
    m = TM[k]; n = i(m.sum())
    if n == 0: terms_out[k] = dict(**meta, n=0); continue
    cr = pd.Series(m).groupby(st.reg.values).sum().reindex(Nreg.index, fill_value=0)
    lq = (cr / n) / shreg
    cl = pd.Series(m).groupby(st.la_code.values).sum()
    clr = (cl / Nla.reindex(cl.index)).sort_values(ascending=False)
    clr = clr[cl.reindex(clr.index) >= 3]
    terms_out[k] = dict(**meta, n=n, per_10k=round(n / len(st) * 1e4, 2),
        nation={nn: i(cr.get(nn, 0)) if nn != "England" else i(cr[[g for g in cr.index if g not in NATIONS]].sum()) for nn in NATIONS},
        top_region=[lq.idxmax(), round(float(lq.max()), 1), r3(cr.max() / n)],
        regions={g: i(c) for g, c in cr.items()},
        top_councils=[[lanm[c], i(cl[c]), round(float(v * 1e4), 1)] for c, v in clr.head(5).items()])
R["terms"] = terms_out
# automatic ranking: the most regional street words (ending or first word, at least 150 streets)
rows = []
def conc(mask):
    c = pd.Series(mask).groupby(st.reg.values).sum().reindex(Nreg.index, fill_value=0); lq = (c / c.sum()) / shreg
    return lq.idxmax(), float(lq.max()), float(c.max() / c.sum())
for g, n in st[st.generic != ""].generic.value_counts().items():
    if n < 150: break
    reg, lqv, shv = conc((st.generic == g).values); rows.append(dict(word=g, kind="ending", n=i(n), region=reg, lq=round(lqv, 1), share=r3(shv)))
for w, n in st.first.value_counts().items():
    if n < 150: break
    if w in {"the", "st", "st.", "saint", "old", "new", "upper", "lower", "north", "south", "east", "west", "great", "little", "high", "far", "near", "y"}: continue
    reg, lqv, shv = conc((st.first == w).values); rows.append(dict(word=w.title(), kind="first word", n=i(n), region=reg, lq=round(lqv, 1), share=r3(shv)))
rw = pd.DataFrame(rows).sort_values("lq", ascending=False)
rw.to_csv(os.path.join(DATA, "regional_words.csv"), index=False)
R["regional_words_top"] = rw.head(40).to_dict("records")
R["regional_words_by_region"] = {g: rw[rw.region == g].head(6)[["word", "kind", "n", "lq", "share"]].to_dict("records") for g in Nreg.index }

# ---------------- royals ----------------
R["royal"] = {k: i(TM[k].sum()) for k in ["w_victoria", "w_albert", "w_queen", "w_king", "w_george", "w_elizabeth", "w_coronation", "w_jubilee"]}

# ---------------- signature names by council ----------------
nat_name = st.name.value_counts()
cnt = st.groupby(["la_code", "name"]).size().rename("c").reset_index()
cnt["N"] = cnt.la_code.map(Nla); cnt["T"] = cnt.name.map(nat_name)
cnt["lq"] = (cnt.c / cnt.N) / (cnt["T"] / len(st))
sig = cnt[(cnt.c >= 4) & (cnt["T"] >= 25)].sort_values("lq", ascending=False).groupby("la_code").head(1).set_index("la_code")
mc = cnt.sort_values(["c", "T"], ascending=[False, False]).groupby("la_code").head(1).set_index("la_code")
lat = pd.DataFrame(dict(la_name=lanm, nation=st.groupby("la_code").nat.first(), streets=Nla,
    top_name=mc.name, top_count=mc.c, signature=sig.name, signature_count=sig.c, signature_uk=sig["T"], signature_lq=sig.lq.round(1),
    high_street=la.set_index("la_code").high, main_street=la.set_index("la_code").main))
for k in TM:
    lat["t_" + k] = pd.Series(TM[k]).groupby(st.la_code.values).sum().reindex(lat.index).fillna(0).astype(int)
lat.index.name = "la_code"
lat.to_csv(os.path.join(DATA, "councils.csv"))
tops = lat.top_name.value_counts()
R["council_top_names"] = [[n, i(c)] for n, c in tops.head(12).items()]
R["council_top_names_n"] = i(len(tops))
R["signature_examples"] = {lanm[c]: [r["name"], i(r.c), i(r["T"]), round(float(r.lq), 1)] for c, r in sig.iterrows()}

# ---------------- 10 km and 20 km cells ----------------
def cells(size):
    cx = (st.x // size).astype(int); cy = (st.y // size).astype(int)
    key = cx.astype(str) + "_" + cy.astype(str)
    df = pd.DataFrame(dict(cx=cx, cy=cy, key=key, name=st.name, nat=st.nat))
    g = df.groupby("key")
    out = pd.DataFrame(dict(cx=g.cx.first(), cy=g.cy.first(), n=g.size(), nation=g.nat.agg(lambda s: s.value_counts().index[0])))
    for k in TM: out[k] = pd.Series(TM[k]).groupby(key.values).sum().reindex(out.index).fillna(0).astype(int)
    c = df.groupby(["key", "name"]).size().rename("c").reset_index().sort_values(["key", "c"], ascending=[True, False])
    c["T"] = c.name.map(nat_name)
    c = c.sort_values(["key", "c", "T"], ascending=[True, False, False])
    topn = c.groupby("key").head(8)
    tp = {}
    for a, b, k in zip(topn.name.values, topn.c.values, topn.key.values): tp.setdefault(k, []).append([a, i(b)])
    out["top"] = pd.Series(tp)
    return out, c
c10, cc10 = cells(10000); c20, cc20 = cells(20000)
c10.drop(columns=["top"]).to_csv(os.path.join(DATA, "cells_10km.csv"))
R["cells"] = dict(n10=i(len(c10)), n20=i(len(c20)))
# main-street word per 20 km cell with at least 3 of the five
fw = ["high_street", "main_street", "the_street", "fore_street", "front_street"]
sub = c20[c20[fw].sum(axis=1) >= 3]
R["cells"]["main_word_20km"] = {k: i((sub[fw].idxmax(1) == k).sum()) for k in fw}
R["cells"]["main_word_20km_n"] = i(len(sub))
# top name per 20 km cell (cells with at least 50 streets)
big = c20[c20.n >= 50]
t20 = big["top"].map(lambda t: t[0][0]).value_counts()
R["cells"]["top_name_20km"] = [[a, i(b)] for a, b in t20.head(12).items()]
R["cells"]["top_name_20km_n"] = i(len(big))

# ---------------- regional stories checked against data ----------------
def share_in(k, regs):
    m = TM[k]; return r3(m[st.reg.isin(regs).values].sum() / m.sum())
R["stories"] = dict(
    the_street_east=share_in("the_street", ["Eastern", "South East"]),
    fore_street_sw=share_in("fore_street", ["South West"]),
    front_street_ne=share_in("front_street", ["North East"]),
    wynd_scot=share_in("r_wynd", ["Scotland"]), brae_scot=share_in("r_brae", ["Scotland"]),
    loke_east=share_in("r_loke", ["Eastern"]), twitten_se=share_in("r_twitten", ["South East"]),
    gate_yorks_em=share_in("r_gate", ["Yorkshire and the Humber", "East Midlands", "North East", "North West"]),
    garth_yorks=share_in("r_garth", ["Yorkshire and the Humber"]), fold_nw=share_in("r_fold", ["North West", "Yorkshire and the Humber"]),
    brow_nw=share_in("r_brow", ["North West"]), drove_east=share_in("r_drove", ["Eastern", "East Midlands"]),
    chare_ne=share_in("r_chare", ["North East"]), manse_scot_ni=share_in("manse_road", ["Scotland", "Northern Ireland"]),
    kirk_scot=share_in("w_kirk", ["Scotland"]),
    welsh_any_wales=r3(TM["cy_any"][(st.nat == "Wales").values].sum() / (st.nat == "Wales").sum()),
    welsh_any_n=i(TM["cy_any"].sum()), irish_ni_share=r3(TM["ga_any"].sum() / (st.nat == "Northern Ireland").sum()),
    gaelic_n=i(TM["gd_any"].sum()), close_share=r3((st.generic == "Close").mean()),
    close_ni=r3(((st.generic == "Close") & (st.nat == "Northern Ireland")).sum() / (st.nat == "Northern Ireland").sum()),
    park_ni=r3(((st.generic == "Park") & (st.nat == "Northern Ireland")).sum() / (st.nat == "Northern Ireland").sum()),
    park_gb=r3(((st.generic == "Park") & (st.nat != "Northern Ireland")).sum() / (st.nat != "Northern Ireland").sum()),
)
R["term_keys"] = [k for k in TL]
json.dump(R, open(os.path.join(DATA, "results.json"), "w"), indent=1, ensure_ascii=False)
st[["kind"]].to_pickle(os.path.join(WORK, "kind.pkl.gz"), compression="gzip")
c10.to_pickle(os.path.join(WORK, "c10.pkl")); c20.to_pickle(os.path.join(WORK, "c20.pkl"))
json.dump(TL, open(os.path.join(WORK, "terms.json"), "w"), ensure_ascii=False)
print(json.dumps({k: R[k] for k in ["meta", "hm", "stories", "royal", "cells", "council_top_names"]}, ensure_ascii=False)[:6000])
