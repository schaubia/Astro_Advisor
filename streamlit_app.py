import streamlit as st
import ephem
import math
import requests
import csv
import os
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="AstroAdvisor", page_icon="🔭", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif;background-color:#050a14;color:#c9d6e8}
.stApp{background:radial-gradient(ellipse at 20% 10%,#0d1f3c 0%,#050a14 60%),radial-gradient(ellipse at 80% 90%,#0a1628 0%,transparent 60%);background-color:#050a14}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:#e8f0ff!important}
[data-testid="stSidebar"]{background:rgba(8,18,38,.95)!important;border-right:1px solid rgba(100,150,255,.15)!important}
.stButton>button{background:linear-gradient(135deg,#1a3a6e,#0d5cb5)!important;color:#e8f0ff!important;border:1px solid rgba(100,180,255,.4)!important;border-radius:4px!important;font-family:'Space Mono',monospace!important;font-size:13px!important;letter-spacing:1px!important;transition:all .2s!important;width:100%}
.stButton>button:hover{background:linear-gradient(135deg,#1e4585,#1269cc)!important;transform:translateY(-1px)!important;box-shadow:0 4px 20px rgba(50,120,255,.3)!important}
.target-card{background:rgba(12,25,55,.7);border:1px solid rgba(80,130,220,.2);border-radius:8px;padding:1.2rem 1.4rem;margin-bottom:.8rem;position:relative;overflow:hidden}
.target-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,rgba(100,180,255,.6),transparent)}
.card-title{font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;color:#7eb8ff;margin:0 0 .3rem}
.card-type{font-size:.72rem;font-family:'Space Mono',monospace;color:#4a7ab5;text-transform:uppercase;letter-spacing:2px;margin-bottom:.6rem}
.card-desc{font-size:.88rem;color:#9ab0cc;line-height:1.55;margin-bottom:.5rem}
.card-tip{font-size:.85rem;color:#5a7fa0;font-style:italic;margin-bottom:.7rem}
.card-meta{display:flex;gap:.6rem;flex-wrap:wrap}
.meta-pill{font-family:'Space Mono',monospace;font-size:.72rem;color:#5a8fc0;background:rgba(50,100,200,.12);border:1px solid rgba(80,130,220,.2);border-radius:20px;padding:2px 10px}
.section-header{font-family:'Space Mono',monospace;font-size:.75rem;letter-spacing:3px;text-transform:uppercase;color:#3a6699;margin:1.5rem 0 .8rem;padding-bottom:.4rem;border-bottom:1px solid rgba(60,100,180,.2)}
.hero-title{font-family:'Syne',sans-serif;font-weight:800;font-size:2.8rem;color:#e8f0ff;letter-spacing:-2px;line-height:1.1;margin-bottom:.3rem}
.hero-sub{font-family:'Space Mono',monospace;font-size:.8rem;color:#3a6699;letter-spacing:2px;margin-bottom:1.5rem}
.warn-box{background:rgba(30,20,5,.8);border:1px solid rgba(220,150,40,.3);border-radius:6px;padding:.8rem 1.2rem;color:#c8943a;font-family:'Space Mono',monospace;font-size:.8rem;margin-bottom:1rem}
.info-box{background:rgba(5,20,50,.8);border:1px solid rgba(80,130,220,.25);border-radius:6px;padding:.8rem 1.2rem;color:#5a8fc0;font-family:'Space Mono',monospace;font-size:.78rem;margin-bottom:1rem}
label,.stLabel{color:#6a8fc0!important;font-family:'Space Mono',monospace!important;font-size:.78rem!important}
hr{border-color:rgba(80,130,220,.15)!important}
.seeing-panel{background:rgba(8,20,48,.8);border:1px solid rgba(80,130,220,.2);border-radius:10px;padding:1.2rem 1.4rem;margin-bottom:1.5rem}
.seeing-badge{display:inline-block;font-family:'Space Mono',monospace;font-size:.8rem;padding:.35rem 1rem;border-radius:20px;font-weight:700;margin-bottom:.3rem}
.catalog-badge{font-family:'Space Mono',monospace;font-size:.65rem;color:#2a4a7a;background:rgba(20,40,90,.5);border:1px solid rgba(60,100,180,.2);border-radius:12px;padding:1px 8px;margin-left:6px;vertical-align:middle}
</style>
""", unsafe_allow_html=True)

# ── Type mapping ───────────────────────────────────────────────────────────────
TYPE_MAP = {
    "nebula":  "nebulae",
    "galaxy":  "galaxies",
    "cluster": "clusters",
}
FILTER_SUBTYPES = {
    "nebulae":  ["emission","planetary","supernova_remnant","reflection","dark"],
    "galaxies": ["spiral","elliptical","irregular","interacting"],
    "clusters": ["globular","open"],
}

# ── Load CSV catalog ───────────────────────────────────────────────────────────
CATALOG_PATH = os.path.join(os.path.dirname(__file__), "dso_catalog.csv")

@st.cache_data
def load_csv_catalog():
    objects = []
    try:
        with open(CATALOG_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                row["size_arcmin"] = float(row["size_arcmin"])
                row["mag"]         = float(row["mag"])
                row["filter_boost"]= row["filter_boost"].strip().lower() == "true"
                row["_source"]     = "catalog"
                objects.append(row)
    except FileNotFoundError:
        pass
    return objects

# ── Astroquery live search ─────────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_simbad(query_type: str, subtype: str, extra_filter: str = ""):
    """Query Simbad for objects by type. Returns list of dicts matching catalog schema."""
    try:
        from astroquery.simbad import Simbad
        import astropy.units as u

        s = Simbad()
        s.add_votable_fields("otype", "ra(d)", "dec(d)", "flux(V)", "dim_majaxis", "sp_type")
        s.TIMEOUT = 15

        # Simbad otype codes
        otype_map = {
            "emission":          "HII",
            "planetary":         "PN",
            "supernova_remnant": "SNR",
            "reflection":        "RNe",
            "globular":          "GlC",
            "open":              "OpC",
            "spiral":            "G",
            "elliptical":        "G",
            "irregular":         "G",
            "galaxy":            "G",
        }
        otype = otype_map.get(subtype, "")
        if not otype:
            return []

        result = s.query_criteria(f"otype='{otype}'", wildcard=True)
        if result is None:
            return []

        objects = []
        for row in result:
            try:
                ra_deg  = float(row["RA_d"])
                dec_deg = float(row["DEC_d"])
                mag     = float(row["FLUX_V"]) if row["FLUX_V"] else 12.0
                size    = float(row["GALDIM_MAJAXIS"]) if row["GALDIM_MAJAXIS"] else 5.0
                name    = str(row["MAIN_ID"]).strip()

                # convert RA degrees to HH:MM:SS string
                ra_h = ra_deg / 15
                ra_hh = int(ra_h)
                ra_mm = int((ra_h - ra_hh) * 60)
                ra_ss = ((ra_h - ra_hh) * 60 - ra_mm) * 60
                ra_str = f"{ra_hh}:{ra_mm:02d}:{ra_ss:04.1f}"

                dec_sign = "+" if dec_deg >= 0 else "-"
                dec_abs  = abs(dec_deg)
                dec_dd   = int(dec_abs)
                dec_mm   = int((dec_abs - dec_dd) * 60)
                dec_str  = f"{dec_sign}{dec_dd}:{dec_mm:02d}"

                objects.append({
                    "name":         name,
                    "full_name":    name,
                    "ra":           ra_str,
                    "dec":          dec_str,
                    "size_arcmin":  size,
                    "mag":          mag,
                    "type":         query_type,
                    "subtype":      subtype,
                    "constellation":"",
                    "filter_boost": subtype in ["emission","planetary","supernova_remnant","dark"],
                    "why":          f"Live result from Simbad — {subtype} object.",
                    "tip":          "Check object size vs your FOV before shooting.",
                    "_source":      "simbad",
                })
            except Exception:
                continue
        return objects
    except Exception as e:
        return []

# ── Sky math ──────────────────────────────────────────────────────────────────
def get_altitude(ra, dec, lat, lon):
    dt = datetime.now(timezone.utc)
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.elevation = 600
    obs.date = dt.strftime("%Y/%m/%d %H:%M:%S")
    obs.pressure = 0
    b = ephem.FixedBody()
    b._ra  = ephem.hours(ra)
    b._dec = ephem.degrees(dec)
    b.compute(obs)
    return math.degrees(float(b.alt))

def moon_phase():
    m = ephem.Moon()
    m.compute(datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S"))
    return m.phase

def fov_fill(size_arcmin, focal_mm, sensor_mm=23.5):
    fov_arcmin = 2 * math.degrees(math.atan(sensor_mm / 2 / focal_mm)) * 60
    return size_arcmin / fov_arcmin * 100

# ── FOV visual diagram ──────────────────────────────────────────────────────────
FOV_COLORS = {"nebula": "#9a6ff0", "galaxy": "#f0a15a", "cluster": "#5adba0"}
FOV_RATIO  = {  # width:height style ratio per subtype (visual approximation only,
                # real objects don't have known position angle in this catalog)
    "spiral": 0.42, "interacting": 0.45, "irregular": 0.55, "elliptical": 0.75,
    "dark": 0.35, "supernova_remnant": 0.6,
}

def render_fov_svg(obj, focal_mm, uid, sensor_w_mm=23.5, sensor_h_mm=15.6):
    fov_w_arcmin = 2 * math.degrees(math.atan(sensor_w_mm / 2 / focal_mm)) * 60
    fov_h_arcmin = 2 * math.degrees(math.atan(sensor_h_mm / 2 / focal_mm)) * 60

    box_w = 150.0
    box_h = box_w * (fov_h_arcmin / fov_w_arcmin)
    scale = box_w / fov_w_arcmin  # px per arcmin

    size = obj["size_arcmin"]
    ratio = FOV_RATIO.get(obj.get("subtype", ""), 0.85)
    obj_w_px = max(3.0, size * scale)
    obj_h_px = obj_w_px * ratio

    cx, cy = box_w / 2, box_h / 2
    color = FOV_COLORS.get(obj.get("type", ""), "#7eb8ff")
    fill_pct = fov_fill(size, focal_mm)
    overflow = obj_w_px > box_w or obj_h_px > box_h
    caption = "extends beyond frame — mosaic needed" if overflow else f"{fill_pct:.0f}% frame fill"

    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:.25rem;">
      <svg width="{box_w}" height="{box_h}" viewBox="0 0 {box_w} {box_h}" style="background:rgba(4,10,24,.6);border-radius:4px;">
        <defs><clipPath id="clip{uid}"><rect x="0" y="0" width="{box_w}" height="{box_h}"/></clipPath></defs>
        <rect x="1" y="1" width="{box_w-2}" height="{box_h-2}" fill="none" stroke="#3a6699" stroke-width="1.2" stroke-dasharray="4,3"/>
        <ellipse cx="{cx}" cy="{cy}" rx="{obj_w_px/2:.1f}" ry="{obj_h_px/2:.1f}" fill="{color}" fill-opacity="0.35" stroke="{color}" stroke-width="1" clip-path="url(#clip{uid})"/>
      </svg>
      <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#4a7ab5;text-align:center;max-width:150px;">{caption}</div>
    </div>
    """

def score_obj(obj, lat, lon, focal_mm, moon_pct, has_filter):
    try:
        alt = get_altitude(obj["ra"], obj["dec"], lat, lon)
    except Exception:
        return None, 0
    if alt < 15:
        return None, alt
    a = min(100, 55 + (alt - 45) * 0.8) if alt >= 45 else (alt - 15) / 30 * 55
    fill = fov_fill(obj["size_arcmin"], focal_mm)
    f = 100 if 8 <= fill <= 70 else (max(0, fill / 8 * 60) if fill < 8 else max(30, 100 - (fill - 70) * 0.8))
    penalty = (moon_pct / 100) * 30
    if has_filter and obj["filter_boost"]:
        penalty *= 0.25
    return round(a * 0.5 + f * 0.4 - penalty, 1), round(alt, 1)

def get_difficulty(obj, focal_mm, moon_pct, has_filter):
    fill = fov_fill(obj["size_arcmin"], focal_mm)
    if obj["mag"] > 9.5 or (moon_pct > 50 and not (has_filter and obj["filter_boost"])):
        return "Advanced", "#c84040"
    if obj["mag"] > 7.5 or fill < 5 or fill > 80:
        return "Intermediate", "#c8a020"
    return "Beginner", "#3a9e5f"

def build_why(obj, alt, focal_mm, moon_pct, has_filter):
    parts = [obj["why"]]
    if alt >= 60:
        parts.append(f"Excellent altitude at {alt:.0f}° tonight.")
    elif alt >= 35:
        parts.append(f"Good altitude at {alt:.0f}°.")
    else:
        parts.append(f"Low at {alt:.0f}° — image near transit.")
    fill = fov_fill(obj["size_arcmin"], focal_mm)
    if fill < 5:
        parts.append(f"Small for this focal length ({fill:.0f}% frame fill).")
    elif fill > 75:
        parts.append(f"Large object ({fill:.0f}% frame fill) — mosaic or shorter FL needed.")
    else:
        parts.append(f"Good FOV fit at {fill:.0f}% frame fill.")
    if moon_pct > 60 and obj["filter_boost"]:
        parts.append("Narrowband filter will save this shot from the bright moon." if has_filter else f"Moon at {moon_pct:.0f}% — a filter would help significantly.")
    return " ".join(parts)

# ── Seeing forecast ────────────────────────────────────────────────────────────
SEEING_LABELS = ["Very poor","Poor","Fair","Good","Very good","Excellent"]
SEEING_COLORS = ["#8b1a1a","#c84040","#c8843a","#c8b820","#3a9e5f","#3a7acc"]

def seeing_score(cloud, wind, precip, humidity):
    if cloud > 85 or precip > 40:
        return 0.0
    s = 5.0 - cloud/100*2.5 - min(wind,30)/30*1.5 - precip/100*1.5 - max(0,humidity-70)/30*0.5
    return round(max(0.0, min(5.0, s)), 2)

@st.cache_data(ttl=1800)
def fetch_seeing(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "cloud_cover,wind_speed_10m,precipitation_probability,relative_humidity_2m,temperature_2m",
        "current": "cloud_cover,wind_speed_10m,precipitation_probability,relative_humidity_2m,temperature_2m",
        "forecast_days": 2, "timezone": "auto",
    }
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        d = r.json()
    except Exception as e:
        return None, str(e)

    hourly  = d["hourly"]
    current = d.get("current", {})
    curr_score = seeing_score(current.get("cloud_cover",50), current.get("wind_speed_10m",10),
                              current.get("precipitation_probability",0), current.get("relative_humidity_2m",60))
    now_utc = datetime.now(timezone.utc)
    results = []
    for i, t_str in enumerate(hourly["time"]):
        try:
            t = datetime.fromisoformat(t_str)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if t < now_utc - timedelta(hours=1): continue
        if len(results) >= 12: break
        results.append({
            "time":  t_str[-5:],
            "score": seeing_score(hourly["cloud_cover"][i], hourly["wind_speed_10m"][i],
                                  hourly["precipitation_probability"][i], hourly["relative_humidity_2m"][i]),
            "cloud": hourly["cloud_cover"][i], "wind": hourly["wind_speed_10m"][i],
            "precip": hourly["precipitation_probability"][i], "humidity": hourly["relative_humidity_2m"][i],
        })
    return {"current_score": curr_score,
            "current_cloud": current.get("cloud_cover","?"), "current_wind": current.get("wind_speed_10m","?"),
            "current_humidity": current.get("relative_humidity_2m","?"), "current_temp": current.get("temperature_2m","?"),
            "hourly": results}, None

def render_seeing_panel(lat, lon):
    data, err = fetch_seeing(lat, lon)
    st.markdown('<div class="seeing-panel">', unsafe_allow_html=True)
    st.markdown('<div style="font-family:\'Space Mono\',monospace;font-size:.72rem;letter-spacing:3px;text-transform:uppercase;color:#3a6699;margin-bottom:1rem;">🌬 ASTRONOMICAL SEEING FORECAST</div>', unsafe_allow_html=True)
    if err or data is None:
        st.markdown(f'<div style="font-family:\'Space Mono\',monospace;font-size:.78rem;color:#4a6a9a;font-style:italic;">Could not load forecast. Check connection.<br>{err}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return
    cs  = data["current_score"]
    ci  = min(5, int(round(cs)))
    col_badge, col_stats = st.columns([1, 3])
    with col_badge:
        stars = "★"*ci + "☆"*(5-ci)
        st.markdown(f"""<div style="text-align:center;padding:.5rem;">
          <div style="font-family:'Space Mono',monospace;font-size:.65rem;color:#3a5a8a;letter-spacing:2px;margin-bottom:.4rem;">NOW</div>
          <div class="seeing-badge" style="background:{SEEING_COLORS[ci]}22;color:{SEEING_COLORS[ci]};border:1px solid {SEEING_COLORS[ci]}55;">{SEEING_LABELS[ci]}</div>
          <div style="font-family:'Space Mono',monospace;font-size:.9rem;color:{SEEING_COLORS[ci]};margin-top:.2rem;">{stars}</div>
          <div style="font-family:'Space Mono',monospace;font-size:.7rem;color:#3a5a8a;margin-top:.2rem;">{cs:.1f} / 5.0</div>
        </div>""", unsafe_allow_html=True)
    with col_stats:
        st.markdown(f"""<div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-top:.5rem;">
          <div style="font-family:'Space Mono',monospace;font-size:.75rem;color:#4a7ab5;">☁ Clouds <span style="color:#7eb8ff;font-weight:700;">{data['current_cloud']}%</span></div>
          <div style="font-family:'Space Mono',monospace;font-size:.75rem;color:#4a7ab5;">💨 Wind <span style="color:#7eb8ff;font-weight:700;">{data['current_wind']} km/h</span></div>
          <div style="font-family:'Space Mono',monospace;font-size:.75rem;color:#4a7ab5;">💧 Humidity <span style="color:#7eb8ff;font-weight:700;">{data['current_humidity']}%</span></div>
          <div style="font-family:'Space Mono',monospace;font-size:.75rem;color:#4a7ab5;">🌡 Temp <span style="color:#7eb8ff;font-weight:700;">{data['current_temp']}°C</span></div>
        </div>""", unsafe_allow_html=True)
    if data["hourly"]:
        bars = '<div style="display:flex;gap:3px;align-items:flex-end;height:90px;padding:.5rem .2rem 0;margin-top:.8rem;">'
        for h in data["hourly"]:
            s   = h["score"]
            idx = min(5, int(round(s)))
            clr = SEEING_COLORS[idx]
            bh  = int(s / 5 * 70) + 4
            bars += f"""<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:2px;">
              <div style="font-family:'Space Mono',monospace;font-size:.55rem;color:{clr};">{s:.1f}</div>
              <div style="width:100%;background:rgba(30,50,100,.3);border-radius:3px;height:70px;display:flex;align-items:flex-end;overflow:hidden;">
                <div style="width:100%;height:{bh}px;background:{clr};border-radius:3px;opacity:.85;"></div>
              </div>
              <div style="font-family:'Space Mono',monospace;font-size:.55rem;color:#2a4a7a;">{h['time']}</div>
            </div>"""
        bars += '</div>'
        st.markdown(bars, unsafe_allow_html=True)
        st.markdown("""<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-top:.6rem;padding-top:.5rem;border-top:1px solid rgba(60,100,180,.15);">
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#1e3a5f;">SCORE:</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#8b1a1a;">0-1 Very poor</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#c84040;">1-2 Poor</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#c8843a;">2-3 Fair</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#c8b820;">3-4 Good</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#3a9e5f;">4-5 Very good</span>
          <span style="font-family:'Space Mono',monospace;font-size:.65rem;color:#3a7acc;">5 Excellent</span>
        </div>
        <div style="font-family:'Space Mono',monospace;font-size:.6rem;color:#1a2e50;margin-top:.3rem;">
          Cloud cover · wind · precip · humidity · Data: Open-Meteo (free, no key)
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">✦ AstroAdvisor</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">DEEP SKY TARGET PLANNER · NO API KEY NEEDED</div>', unsafe_allow_html=True)

EQUIPMENT = {
    "RedCat 51 (250mm f/4.9)":        {"focal": 250,  "aperture": 51},
    "Refractor 80mm ED (480mm f/6)":  {"focal": 480,  "aperture": 80},
    "Refractor 80mm (600mm f/7.5)":   {"focal": 600,  "aperture": 80},
    "Refractor 102mm (714mm f/7)":    {"focal": 714,  "aperture": 102},
    "Newtonian 150mm (750mm f/5)":    {"focal": 750,  "aperture": 150},
    'SCT 8" (2032mm f/10)':           {"focal": 2032, "aperture": 203},
    'Dobsonian 10" (1200mm f/4.7)':   {"focal": 1200, "aperture": 254},
    "Custom": None,
}

BORTLE_LABELS = {
    1: "1 · Excellent dark sky",
    2: "2 · Typical dark sky",
    3: "3 · Rural sky",
    4: "4 · Rural/suburban transition",
    5: "5 · Suburban sky",
    6: "6 · Bright suburban sky",
    7: "7 · Suburban/urban transition",
    8: "8 · City sky",
    9: "9 · Inner-city sky",
}

def recommend_integration(obj, f_ratio, bortle, has_filter):
    """Heuristic estimate of how many light frames / how much integration
    time a target needs, given its magnitude, the sky darkness (Bortle),
    and the optical speed (f-ratio) of the equipment in use.

    This is a rule-of-thumb planning aid, not a precise SNR calculator —
    real needs vary with camera read noise, QE, and actual sky conditions.
    """
    mag = obj["mag"]

    # Fainter objects need more integration; ~1.4x per magnitude step
    # relative to a mag 8 / Bortle 4 / f5 / no-filter baseline of 3h.
    mag_factor = 1.4 ** (mag - 8)

    # Brighter (higher-number) Bortle skies swamp signal with background
    # glow, requiring more integration to reach the same SNR.
    bortle_factor = 1.25 ** (bortle - 4)

    # A narrowband/UHC filter suppresses skyglow, so it blunts most of
    # the Bortle penalty for targets that respond to it.
    if has_filter and obj.get("filter_boost"):
        bortle_factor = 1 + (bortle_factor - 1) * 0.4

    # Faster optics (lower f-ratio) collect light quicker; time scales
    # roughly with the square of the f-ratio, relative to f/5.
    speed_factor = (f_ratio / 5.0) ** 2

    total_hours = 3.0 * mag_factor * bortle_factor * speed_factor
    total_hours = max(0.5, min(20.0, total_hours))

    # Recommended single-sub length: shorter under brighter skies to
    # avoid the background swamping the sub before it saturates.
    if bortle <= 3:
        sub_length = 300
    elif bortle <= 5:
        sub_length = 180
    elif bortle <= 7:
        sub_length = 120
    else:
        sub_length = 60

    # Very bright cores need shorter subs regardless of sky darkness.
    if mag < 5:
        sub_length = min(sub_length, 60)

    # A narrowband filter lets you push subs longer before sky-limiting.
    if has_filter and obj.get("filter_boost"):
        sub_length = int(sub_length * 1.5)

    num_subs = max(1, math.ceil(total_hours * 3600 / sub_length))
    actual_hours = num_subs * sub_length / 3600

    return {
        "total_hours":  total_hours,
        "sub_length":   sub_length,
        "num_subs":     num_subs,
        "actual_hours": actual_hours,
    }

with st.sidebar:
    st.markdown("### 📍 Location")
    lat = st.number_input("Latitude",  value=42.62, format="%.4f", step=0.01)
    lon = st.number_input("Longitude", value=23.23, format="%.4f", step=0.01)
    st.caption("Default: Vladaya / Sofia")
    bortle = st.selectbox("Bortle sky class", list(BORTLE_LABELS.keys()),
                          index=3, format_func=lambda b: BORTLE_LABELS[b],
                          help="How dark your sky is. Higher = more light pollution.")
    st.markdown("---")
    st.markdown("### 🔭 Equipment")
    scope = st.selectbox("Telescope / Lens", list(EQUIPMENT.keys()))
    eq    = EQUIPMENT[scope]
    if eq is None:
        focal_mm    = st.number_input("Focal length (mm)", value=500.0, min_value=50.0, max_value=5000.0)
        aperture_mm = st.number_input("Aperture (mm)",      value=80.0,  min_value=20.0, max_value=1000.0)
    else:
        focal_mm    = float(eq["focal"])
        aperture_mm = float(eq["aperture"])
    f_ratio = focal_mm / aperture_mm
    st.caption(f"f/{f_ratio:.1f}")
    has_filter = st.checkbox("I have a narrowband / UHC filter", value=True)
    st.markdown("---")
    st.markdown("### 🎯 Target types")
    want_neb = st.checkbox("Nebulae",  value=True)
    want_gal = st.checkbox("Galaxies", value=True)
    want_clu = st.checkbox("Clusters", value=True)
    st.markdown("---")
    st.markdown("### 🌐 Catalog source")
    use_simbad = st.checkbox("Extend with live Simbad query", value=False,
                             help="Queries the Simbad astronomical database for additional objects. Requires internet. Results are cached for 1 hour.")
    if use_simbad:
        st.caption("⚠ First query may take 10-20s per object type.")
    st.markdown("---")
    run = st.button("▶  FIND MY TARGETS", use_container_width=True)

moon_pct = moon_phase()
now_utc  = datetime.now(timezone.utc)
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("🌙 Moon",   f"{moon_pct:.0f}%")
c2.metric("📅 Date",   now_utc.strftime("%d %b %Y"))
c3.metric("🕐 UTC",    now_utc.strftime("%H:%M"))
c4.metric("🔭 Focal",  f"{focal_mm:.0f} mm  ·  f/{f_ratio:.1f}")
c5.metric("🌃 Bortle", bortle)
st.markdown("---")

render_seeing_panel(lat, lon)

if not run:
    st.markdown("""<div style="text-align:center;padding:2rem 1rem;color:#2a4a7a;
    font-family:'Space Mono',monospace;font-size:.85rem;letter-spacing:1px;">
    ← Configure your setup then press FIND MY TARGETS</div>""", unsafe_allow_html=True)
    st.stop()

types_wanted = []
if want_neb: types_wanted.append("nebulae")
if want_gal: types_wanted.append("galaxies")
if want_clu: types_wanted.append("clusters")
if not types_wanted:
    st.warning("Select at least one target type.")
    st.stop()

ICONS  = {"nebulae":"🌌","galaxies":"🌀","clusters":"✨"}
LABELS = {"nebulae":"NEBULAE","galaxies":"GALAXIES","clusters":"CLUSTERS"}
TYPE_KEY = {"nebulae":"nebula","galaxies":"galaxy","clusters":"cluster"}

# ── Load catalog ───────────────────────────────────────────────────────────────
csv_objects = load_csv_catalog()
catalog_count = len(csv_objects)

with st.spinner("Computing sky positions..."):
    for ttype in types_wanted:
        # 1. Start with CSV objects of this type
        pool = [o for o in csv_objects if o["type"] == TYPE_KEY[ttype]]

        # 2. Optionally extend with Simbad
        simbad_added = 0
        if use_simbad:
            existing_names = {o["name"].upper() for o in pool}
            for subtype in FILTER_SUBTYPES[ttype]:
                with st.spinner(f"Querying Simbad for {subtype}..."):
                    live = fetch_simbad(TYPE_KEY[ttype], subtype)
                for obj in live:
                    if obj["name"].upper() not in existing_names:
                        pool.append(obj)
                        existing_names.add(obj["name"].upper())
                        simbad_added += 1

        # 3. Score and filter
        scored = []
        for obj in pool:
            s, alt = score_obj(obj, lat, lon, focal_mm, moon_pct, has_filter)
            if s is not None:
                scored.append({**obj, "_score": s, "_alt": alt})
        scored.sort(key=lambda x: x["_score"], reverse=True)
        top5 = scored[:5]

        # Header
        source_note = f"  <span class='catalog-badge'>CSV {catalog_count} obj" + (f" + Simbad +{simbad_added}" if use_simbad and simbad_added else "") + "</span>"
        st.markdown(f'<div class="section-header">{ICONS[ttype]} {LABELS[ttype]} — TOP {len(top5)}{source_note}</div>', unsafe_allow_html=True)

        if not top5:
            st.markdown('<div class="warn-box">No objects above the horizon right now for this type.</div>', unsafe_allow_html=True)
            continue

        for i, obj in enumerate(top5):
            dlabel, dcolor = get_difficulty(obj, focal_mm, moon_pct, has_filter)
            fill = fov_fill(obj["size_arcmin"], focal_mm)
            why  = build_why(obj, obj["_alt"], focal_mm, moon_pct, has_filter)
            src_badge = ""
            if obj.get("_source") == "simbad":
                src_badge = '<span style="font-family:\'Space Mono\',monospace;font-size:.62rem;color:#3a6a3a;background:rgba(20,60,20,.5);border:1px solid rgba(60,150,60,.2);border-radius:10px;padding:1px 7px;margin-left:6px;">live</span>'
            subtype_str = obj.get("subtype","").replace("_"," ").title()
            con_str     = obj.get("constellation","")
            fov_svg     = render_fov_svg(obj, focal_mm, f"{ttype}{i}")
            st.markdown(f"""
            <div class="target-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div class="card-title">#{i+1} &nbsp; {obj.get('full_name', obj['name'])}{src_badge}</div>
                  <div class="card-type">{subtype_str} &nbsp;·&nbsp; {con_str}</div>
                </div>
                <div style="font-family:'Space Mono',monospace;font-size:.72rem;color:{dcolor};
                            border:1px solid {dcolor}44;border-radius:20px;padding:2px 10px;white-space:nowrap;">
                  {dlabel}
                </div>
              </div>
              <div style="display:flex;gap:1rem;align-items:flex-start;margin-top:.4rem;">
                <div style="flex:1;min-width:0;">
                  <div class="card-desc">{why}</div>
                  <div class="card-tip">💡 {obj['tip']}</div>
                  <div class="card-meta">
                    <span class="meta-pill">Alt {obj['_alt']}°</span>
                    <span class="meta-pill">Score {obj['_score']}</span>
                    <span class="meta-pill">{fill:.0f}% frame fill</span>
                    <span class="meta-pill">Mag {obj['mag']}</span>
                    {'<span class="meta-pill">🔴 Filter helps</span>' if obj["filter_boost"] else ''}
                  </div>
                </div>
                <div style="flex-shrink:0;">{fov_svg}</div>
              </div>
            </div>""", unsafe_allow_html=True)

            plan = recommend_integration(obj, f_ratio, bortle, has_filter)
            filter_note = ("narrowband filter applied to this estimate"
                            if has_filter and obj["filter_boost"]
                            else "no filter benefit for this target")
            with st.expander(f"📊 Exposure plan — {plan['num_subs']}× {plan['sub_length']}s subs (≈{plan['actual_hours']:.1f}h total)"):
                st.markdown(f"""
                <div style="font-family:'Space Mono',monospace;font-size:.8rem;color:#9ab0cc;line-height:1.8;">
                  <b style="color:#7eb8ff;">Suggested lights:</b> {plan['num_subs']} × {plan['sub_length']}s subs<br>
                  <b style="color:#7eb8ff;">Total integration:</b> ≈ {plan['actual_hours']:.1f} h ({plan['total_hours']:.1f} h target)<br>
                  <b style="color:#7eb8ff;">Based on:</b> mag {obj['mag']} target · f/{f_ratio:.1f} system · Bortle {bortle} sky · {filter_note}<br>
                  <span style="color:#5a7fa0;font-style:italic;font-size:.75rem;">Heuristic planning estimate, not a precise SNR calculator — actual needs depend on your camera's read noise, QE, and real-world conditions on the night.</span>
                </div>
                """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""<div style="font-family:'Space Mono',monospace;font-size:.72rem;color:#1e3a5f;text-align:center;padding:.5rem;">
  UTC {now_utc.strftime('%Y-%m-%d %H:%M')} · Moon {moon_pct:.0f}% · Focal {focal_mm:.0f}mm f/{f_ratio:.1f} · Bortle {bortle} ·
  {'Narrowband ✓' if has_filter else 'Broadband only'} · Catalog: {catalog_count} objects · Seeing: Open-Meteo
</div>""", unsafe_allow_html=True)
