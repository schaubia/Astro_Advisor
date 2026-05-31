# ✦ AstroAdvisor

**A self-contained deep sky astrophotography target planner — no API key, no paid services needed.**

AstroAdvisor tells you exactly what to photograph tonight based on your location, equipment, and target preference. It computes real-time sky positions, scores each object for altitude, field-of-view fit, moon impact, and filter benefit — then ranks the top 5 nebulae, galaxies, and clusters for your current session. It also shows a live 12-hour astronomical seeing forecast.

---

## Features

- **Real-time sky calculations** — altitude computed for your exact latitude/longitude using `ephem`
- **Equipment-aware FOV scoring** — objects ranked by how well they fit your focal length (APS-C sensor assumed)
- **Moon & filter logic** — narrowband/UHC filter dramatically reduces moon penalty for emission nebulae
- **Difficulty rating** — Beginner / Intermediate / Advanced based on magnitude, FOV fit, and moon conditions
- **Top 5 per object type** — nebulae, galaxies, and clusters ranked independently
- **Astronomical seeing forecast** — 12-hour hourly seeing score derived from cloud cover, wind, precipitation, and humidity via Open-Meteo (free, no key)
- **Bundled CSV catalog** — 109 curated objects, works fully offline
- **Live Simbad extension** — optional toggle to query the Simbad astronomical database for additional objects at runtime
- **Zero dependencies on paid APIs** — runs entirely offline after install (Simbad extension requires internet)
- **Streamlit Cloud ready** — deploy in one click, no secrets needed

---

## Catalog

The bundled `dso_catalog.csv` ships with the app and contains 109 hand-curated objects:

| Type | Count | Subtypes |
|------|-------|---------|
| Nebulae | 39 | Emission, planetary, supernova remnant, reflection, dark |
| Galaxies | 32 | Spiral, elliptical, irregular, interacting |
| Clusters | 38 | Globular, open |

Each entry includes RA/Dec coordinates, angular size, magnitude, constellation, filter recommendation, a "why tonight" description, and a practical shooting tip.

**Extending the catalog** is as simple as adding rows to `dso_catalog.csv` — no code changes needed. The CSV schema is:

```
name, full_name, ra, dec, size_arcmin, mag, type, subtype, constellation, filter_boost, why, tip
```

### Live Simbad Extension

Enable the **"Extend with live Simbad query"** toggle in the sidebar to query the [Simbad astronomical database](https://simbad.cds.unistra.fr/) at runtime. This adds objects beyond the bundled catalog and is particularly useful for less common subtypes. Results are cached for 1 hour per session and labeled with a `live` badge on their card.

> First query per object type may take 10–20 seconds. Requires internet access.

---

## Seeing Forecast

The seeing panel appears at the top of every session and shows:

- **Current conditions badge** — label (Very poor → Excellent), star rating, and numeric score
- **Live stats** — cloud cover %, wind speed, humidity, temperature
- **12-hour bar chart** — colour-coded bars for each hour so you can spot the best imaging window at a glance

The seeing score (0–5) is computed from Open-Meteo weather data:

```
score = 5.0
      − (cloud_cover / 100) × 2.5
      − (wind_speed / 30)   × 1.5
      − (precip_prob / 100) × 1.5
      − (humidity > 70 excess / 30) × 0.5
```

| Score | Label |
|-------|-------|
| 0–1 | Very poor |
| 1–2 | Poor |
| 2–3 | Fair |
| 3–4 | Good |
| 4–5 | Very good |
| 5 | Excellent |

Forecast data is cached for 30 minutes. Data source: [Open-Meteo](https://open-meteo.com) — free, no registration required.

---

## Installation

**Requirements:** Python 3.9+

```bash
pip install -r requirements.txt
```

```bash
streamlit run astro_advisor_free.py
```

The app opens in your browser at `http://localhost:8501`.

> `dso_catalog.csv` must be in the same directory as `astro_advisor_free.py`.

---

## Deploy to Streamlit Community Cloud

1. Push all files to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file to `astro_advisor_free.py`
4. Deploy — no secrets or API keys required

---

## Usage

1. **Set your location** — latitude and longitude (defaults to Vladaya / Sofia, Bulgaria)
2. **Choose your equipment** — select from preset telescope/lens profiles or enter a custom focal length
3. **Filter checkbox** — tick if you have a narrowband or UHC filter
4. **Select target types** — nebulae, galaxies, clusters, or any combination
5. **Simbad toggle** — optionally extend results with live database queries
6. **Press FIND MY TARGETS** — results appear ranked by tonight's score

### Reading the cards

| Field | Meaning |
|---|---|
| **Alt** | Current altitude in degrees (>40° is good, >60° is excellent) |
| **Score** | Combined ranking score (altitude 50% + FOV fit 40% − moon penalty) |
| **% frame fill** | How much of your APS-C frame the object occupies |
| **Mag** | Visual magnitude (lower = brighter) |
| **🔴 Filter helps** | Object responds well to narrowband / UHC filter |
| **Difficulty** | Beginner / Intermediate / Advanced |
| **`live` badge** | Result came from live Simbad query, not the bundled catalog |

---

## Scoring Algorithm

```
Score = (altitude_score × 0.5) + (fov_score × 0.4) − moon_penalty
```

**Altitude score (0–100)**
- Below 15°: excluded entirely
- 15–45°: linear scale 0 → 55
- 45°+: 55 + bonus up to 100

**FOV fit score (0–100)**
- 8–70% frame fill: 100 (ideal)
- Below 8%: penalised (object too small for focal length)
- Above 70%: penalised (object too large for single frame)

**Moon penalty (0–30)**
- Scales linearly with moon illumination %
- Reduced by 75% for filter-boost objects when narrowband filter is selected

---

## Equipment Presets

| Preset | Focal length |
|---|---|
| RedCat 51 (f/4.9) | 250 mm |
| Refractor 80mm ED (f/6) | 480 mm |
| Refractor 80mm (f/7.5) | 600 mm |
| Refractor 102mm (f/7) | 714 mm |
| Newtonian 150mm (f/5) | 750 mm |
| SCT 8" (f/10) | 2032 mm |
| Dobsonian 10" (f/4.7) | 1200 mm |
| Custom | User-defined |

FOV calculation assumes an **APS-C sensor (23.5 mm wide)**. Full-frame or smaller sensors will have different frame fill percentages.

---

## File Structure

```
astro_advisor_free.py   ← main Streamlit application
dso_catalog.csv         ← bundled DSO catalog (109 objects, must be in same folder)
requirements.txt        ← Python dependencies
README.md               ← this file
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `ephem` | Sky position and moon phase calculations |
| `requests` | Open-Meteo seeing forecast fetch |
| `astroquery` | Optional live Simbad catalog queries |
| `astropy` | Required by astroquery |

All packages are free and open-source.

---

## Planned improvements

- Session timeline — chart showing when each object peaks during the night
- Visual FOV overlay — compare object angular size to your frame
- Bortle scale input — refine scoring for your actual sky darkness
- Multiple sensor size profiles (full-frame, Micro 4/3, dedicated astro cameras)
- Export session plan as PDF
- Mosaic planner for large objects

---

## License

MIT — free to use, modify, and deploy.
