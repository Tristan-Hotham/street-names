# High Street or Main Street? The UK's street-name divide

All 913,335 named streets in the United Kingdom mapped by name: where High Street gives way to Main Street, the other names for the main street, and the regional street words from Wynd and Brae to Garth, Brow, Chare and Loke. The interactive page lets you map the High and Main Street divide, the commonest name in each area, any of 79 street words, or any street name in the UK, by 10 km or 20 km square or by council.

**Interactive version:** https://maps.tristanhotham.com/street-names/

**Paper and archived release:** https://doi.org/10.5281/zenodo.23757702

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- 913,335 named streets: 884,116 in Great Britain (OS Open Names, Named Road) and 29,219 in Northern Ireland (built from OpenStreetMap). They share 388,197 names; 75% of names are used by one street only.
- High Street is the commonest name (2,507), then Station Road (2,074), Church Lane (2,005), Church Street (1,573) and Mill Lane (1,415). Main Street is sixth (1,336).
- Main Street outnumbers High Street in Scotland (309 to 206) and Northern Ireland (132 to 32), and in the East Midlands (414 to 324) and Yorkshire and the Humber (244 to 208). London has 54 High Streets and 1 Main Street; Wales 166 and 9.
- It is a town and village divide: in England Main Street is 8% of the pair in towns and 38% in villages; in the East Midlands and Yorkshire 13% and 62%; in Scotland 27% and 78%.
- Regional main streets: The Street (606, 86% in the East of England and South East), Fore Street (181, 90% South West), Front Street (168, 60% North East).
- Regional words: Wynd (981, 89% Scotland), Garth (883, 75% Yorkshire and the Humber), Brow (511, 78% North West), Chare (42, all North East), Loke (187, 99% East of England). 11% of Northern Ireland's streets end in Park, against 0.7% in Great Britain.
- 9,480 streets have a Welsh name or start with a Welsh street word (22% of streets in Wales); 2,399 Northern Ireland streets have an Irish name in OpenStreetMap.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (results embedded; map data loaded from `data/page/`). |
| `header.png` | Social card (1200 by 630). |
| `data/results.json` | Every number used anywhere. |
| `data/councils.csv` | For each of the 361 council areas (ONS local authority districts): streets, commonest name, signature name, High and Main Street counts and counts of every tracked street word (`t_*`). |
| `data/cells_10km.csv` | The same counts for each 10 km square of the British National Grid (`cx`, `cy` in units of 10 km). |
| `data/name_counts.csv.gz` | Every street name with its count in the UK and each nation. |
| `data/regional_words.csv` | Endings and first words used 150 times or more, with their most concentrated region and location quotient. |
| `data/page/` | Compact files for the page: `cells10.json`, `cells20.json`, `councils.json` (simplified boundaries), `land.json`, `places.json`, `terms.json` and `names/*.json` (every street name and its 10 km squares). |
| `code/01_prepare.py` | Reads the two raw bundles, joins OpenStreetMap ways into streets, assigns councils and squares, parses names. |
| `code/02_analyse.py` | All statistics; writes `results.json` and the CSV tables. |
| `code/03_page_data.py` | Page data files and `name_counts.csv.gz`. |
| `code/04_build_site.py` | Fills `code/page_template.html` to make `index.html`. |
| `code/05_figures.py`, `code/figlib.py` | Static figures and the social card (matplotlib). |
| `code/06_paper.py` | Builds the paper PDF from `code/paper_template.tex` with xelatex. |
| `code/07_release.py` | Blog post and metadata, Zenodo folder. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and source, blog post and figures, Zenodo files. |

## Method in brief

- **Great Britain.** OS Open Names (GB CSV, retrieved 2026-10-29), features of local type Named Road. Section Of Named Road features (extra points for parts of a road inside settlements, which refer back to the whole road) are left out.
- **Northern Ireland.** OpenStreetMap via the Overpass API (retrieved 2026-10-29): 66,824 named ways of road types (no paths, tracks or service roads), joined into streets when they share a name and an end node or have ends within 50 m; 441 short groups named as bridges dropped.
- **Areas.** Current ONS local authority districts by point in polygon; 10 km and 20 km National Grid squares; English regions from OS Open Names. Settlement type from the nearest OS Open Names populated place of the same name within 8 km (86% of GB streets matched).
- **Words.** Exact names; endings are the last word when it is one of 128 street words; first words as written. Concentration is a location quotient against each region's share of all streets.

## Known limits

- Ordnance Survey and OpenStreetMap divide streets differently; compare shares, not raw counts, across the Irish Sea. OpenStreetMap is not complete.
- A Named Road is a modelling choice: a long road may be one feature or several.
- Exact matching misses variants (High Road, Upper High Street). Word groups are simple rules; not every George is a king.
- This is a map of today's names, not of when or why they were given.

## How to rerun

Inputs are read in place (paths at the top of `01_prepare.py`): the two Chrome-fetched bundles in `RAW_DIR` (`sn_osnames_roads_gb.json.gz`, `sn_osm_ni_ways_geom.json.gz`, `sn_osm_ni_roads.json.gz` for place nodes), ONS district boundaries (`LTLA`) and OS Open Names populated places (`OSNAMES`, a compact TSV).

```
python3 code/01_prepare.py
python3 code/02_analyse.py
python3 code/03_page_data.py
python3 code/04_build_site.py
FONT_DIR=path/to/fonts python3 code/05_figures.py
python3 code/06_paper.py
python3 code/07_release.py
```

Needs Python 3 with numpy, pandas, shapely, pyproj and matplotlib, and xelatex with TeX Gyre Pagella and Inter for the paper.

## Sources and licences

- **Great Britain streets and places:** OS Open Names, Ordnance Survey. Contains OS data © Crown copyright and database right 2026. Open Government Licence v3.0.
- **Northern Ireland streets and places:** © OpenStreetMap contributors, Open Database Licence 1.0 (https://www.openstreetmap.org/copyright), via the Overpass API.
- **Boundaries:** Office for National Statistics local authority districts, via https://github.com/onsvisual/uk-topojson. Contains OS data © Crown copyright and database right. Open Government Licence v3.0.
- **Map tiles on the page:** Esri.

Code: MIT (see `LICENSE`). Data files that include Northern Ireland (all combined UK tables, `results.json` and `data/page/`) contain OpenStreetMap data and are released under the ODbL 1.0. Text and figures: CC BY 4.0.

## Citation

Hotham, T. (2026) *High Street or Main Street? The United Kingdom's Street-Name Divide*. Zenodo. https://doi.org/10.5281/zenodo.23757702

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
