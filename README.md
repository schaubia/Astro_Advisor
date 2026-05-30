# ✦ AstroAdvisor

**A self-contained deep sky astrophotography target planner — no API key, no paid services needed.**

AstroAdvisor tells you exactly what to photograph tonight based on your location, equipment, and target preference. It computes real-time sky positions, scores each object for altitude, field-of-view fit, moon impact, and filter benefit — then ranks the top 5 nebulae, galaxies, and clusters for your current session.

---

## Features

- **Real-time sky calculations** — altitude computed for your exact latitude/longitude using `ephem`
- **Equipment-aware FOV scoring** — objects are ranked by how well they fit your focal length (APS-C sensor assumed)
- **Moon & filter logic** — narrowband/UHC filter dramatically reduces moon penalty for emission nebulae
- **Difficulty rating** — Beginner / Intermediate / Advanced based on magnitude, FOV fit, and moon conditions
- **Top 5 per object type** — nebulae, galaxies, and clusters ranked independently
- **Zero dependencies on paid APIs** — runs entirely offline after install
- **Streamlit Cloud ready** — deploy in one click, no secrets needed

---

## Catalog

| Type | Objects |
|------|---------|
| Nebulae | 15 (emission, planetary, reflection, supernova remnants) |
| Galaxies | 10 (spirals, edge-ons, interacting pairs) |
| Clusters | 10 (globular and open) |

---

## Installation

### Requirements

- Python 3.9+
- pip

### Install dependencies

```bash
pip install streamlit ephem
```

Or with the requirements file:

```bash
pip install -r requirements.txt
```

### Run locally

```bash
streamlit run astro_advisor_free.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Deploy to Streamlit Community Cloud

1. Push the files to a public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file to `astro_advisor_free.py`
4. Deploy — no secrets or API keys required

---

## Usage

1. **Set your location** — latitude and longitude (defaults to Vladaya / Sofia, Bulgaria)
2. **Choose your equipment** — select from the preset telescope/lens profiles or enter a custom focal length
3. **Filter checkbox** — tick if you have a narrowband or UHC filter (reduces moon penalty for emission nebulae)
4. **Select target types** — nebulae, galaxies, clusters, or any combination
5. **Press FIND MY TARGETS** — results appear ranked by tonight's score

### Reading the cards

Each result card shows:

| Field | Meaning |
|---|---|
| **Alt** | Current altitude in degrees (higher = better, >40° is good) |
| **Score** | Combined ranking score (altitude 50% + FOV fit 40% + moon penalty) |
| **% frame fill** | How much of your APS-C frame the object occupies |
| **Mag** | Visual magnitude (lower = brighter) |
| **🔴 Filter helps** | Object responds well to narrowband / UHC filter |
| **Difficulty** | Beginner / Intermediate / Advanced |

---

## Scoring Algorithm

Each object receives a score from 0–100 based on three factors:

```
Score = (altitude_score × 0.5) + (fov_score × 0.4) − moon_penalty
```

**Altitude score (0–100)**
- Below 15°: excluded entirely
- 15–45°: linear scale 0→55
- 45°+: 55 + bonus up to 100

**FOV fit score (0–100)**
- 8–70% frame fill: 100 (ideal)
- Below 8%: penalised (object too small)
- Above 70%: penalised (object too large for single frame)

**Moon penalty (0–30)**
- Scales linearly with moon illumination percentage
- Reduced by 75% for emission nebulae when a narrowband filter is selected

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

FOV calculation assumes an **APS-C sensor (23.5 mm wide)**. If you use a full-frame or smaller sensor, frame fill percentages will differ.

---

## File Structure

```
astro_advisor_free.py   ← main Streamlit application
requirements.txt        ← Python dependencies
README.md               ← this file
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `ephem` | Astronomical calculations (altitude, moon phase) |

Both are free and open-source.

---

## Planned improvements

- Session timeline — chart showing when each object peaks during the night
- Visual FOV overlay — compare object angular size to your frame
- Bortle scale input — refine scoring for your actual sky darkness
- Full NGC/IC catalog integration via `astroquery`
- Multiple sensor size profiles (full-frame, Micro 4/3)
- Export session plan as PDF

---

## License

MIT — free to use, modify, and deploy.
