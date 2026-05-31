import streamlit as st
import ephem
import math
from datetime import datetime, timezone

st.set_page_config(page_title="AstroAdvisor", page_icon="🔭", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Syne', sans-serif; background-color: #050a14; color: #c9d6e8; }
.stApp { background: radial-gradient(ellipse at 20% 10%, #0d1f3c 0%, #050a14 60%), radial-gradient(ellipse at 80% 90%, #0a1628 0%, transparent 60%); background-color: #050a14; }
h1,h2,h3 { font-family: 'Syne', sans-serif !important; color: #e8f0ff !important; }
[data-testid="stSidebar"] { background: rgba(8,18,38,0.95) !important; border-right: 1px solid rgba(100,150,255,0.15) !important; }
.stButton > button { background: linear-gradient(135deg,#1a3a6e,#0d5cb5) !important; color: #e8f0ff !important; border: 1px solid rgba(100,180,255,0.4) !important; border-radius: 4px !important; font-family: 'Space Mono', monospace !important; font-size: 13px !important; letter-spacing: 1px !important; transition: all 0.2s !important; width: 100%; }
.stButton > button:hover { background: linear-gradient(135deg,#1e4585,#1269cc) !important; transform: translateY(-1px) !important; box-shadow: 0 4px 20px rgba(50,120,255,0.3) !important; }
.target-card { background: rgba(12,25,55,0.7); border: 1px solid rgba(80,130,220,0.2); border-radius: 8px; padding: 1.2rem 1.4rem; margin-bottom: 0.8rem; position: relative; overflow: hidden; }
.target-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, rgba(100,180,255,0.6), transparent); }
.card-title { font-family: 'Space Mono', monospace; font-size: 1rem; font-weight: 700; color: #7eb8ff; margin: 0 0 0.3rem 0; }
.card-type { font-size: 0.72rem; font-family: 'Space Mono', monospace; color: #4a7ab5; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 0.6rem; }
.card-desc { font-size: 0.88rem; color: #9ab0cc; line-height: 1.55; margin-bottom: 0.5rem; }
.card-tip { font-size: 0.85rem; color: #5a7fa0; font-style: italic; margin-bottom: 0.7rem; }
.card-meta { display: flex; gap: 0.6rem; flex-wrap: wrap; }
.meta-pill { font-family: 'Space Mono', monospace; font-size: 0.72rem; color: #5a8fc0; background: rgba(50,100,200,0.12); border: 1px solid rgba(80,130,220,0.2); border-radius: 20px; padding: 2px 10px; }
.section-header { font-family: 'Space Mono', monospace; font-size: 0.75rem; letter-spacing: 3px; text-transform: uppercase; color: #3a6699; margin: 1.5rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid rgba(60,100,180,0.2); }
.hero-title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 2.8rem; color: #e8f0ff; letter-spacing: -2px; line-height: 1.1; margin-bottom: 0.3rem; }
.hero-sub { font-family: 'Space Mono', monospace; font-size: 0.8rem; color: #3a6699; letter-spacing: 2px; margin-bottom: 2rem; }
.warn-box { background: rgba(30,20,5,0.8); border: 1px solid rgba(220,150,40,0.3); border-radius: 6px; padding: 0.8rem 1.2rem; color: #c8943a; font-family: 'Space Mono', monospace; font-size: 0.8rem; margin-bottom: 1rem; }
label, .stLabel { color: #6a8fc0 !important; font-family: 'Space Mono', monospace !important; font-size: 0.78rem !important; }
hr { border-color: rgba(80,130,220,0.15) !important; }
</style>
""", unsafe_allow_html=True)

DSO = {
  "nebulae": [
    {"name":"M42","full":"M42 – Orion Nebula","ra":"5:35:17","dec":"-5:23","size":85,"mag":4.0,"con":"Orion","filter_boost":True,"why":"The brightest emission nebula in the sky. Enormous at 85 arcmin — fills any wide-field frame.","tip":"Short subs (30-60s) to avoid core overexposure. Ha filter brings out incredible detail."},
    {"name":"M8","full":"M8 – Lagoon Nebula","ra":"18:03:37","dec":"-24:23","size":90,"mag":6.0,"con":"Sagittarius","filter_boost":True,"why":"Large, bright emission nebula. Pairs with M20 in one wide-field frame.","tip":"Frame M8 and M20 together. Ha or UHC filter will reduce skyglow from the south."},
    {"name":"M20","full":"M20 – Trifid Nebula","ra":"18:02:23","dec":"-23:02","size":28,"mag":6.3,"con":"Sagittarius","filter_boost":True,"why":"Unique mix of emission, reflection, and dark lanes. Same field of view as M8.","tip":"Use OIII alongside Ha to reveal the blue reflection lobe."},
    {"name":"M17","full":"M17 – Omega Nebula","ra":"18:20:26","dec":"-16:10","size":46,"mag":6.0,"con":"Sagittarius","filter_boost":True,"why":"One of the brightest emission nebulae. Swan-shaped core is striking even in short exposures.","tip":"Center on the bright swan shape. Ha filter makes this pop."},
    {"name":"M16","full":"M16 – Eagle Nebula","ra":"18:18:48","dec":"-13:47","size":35,"mag":6.4,"con":"Serpens","filter_boost":True,"why":"Home of the Pillars of Creation. Rich star cluster embedded in glowing gas.","tip":"Ha+OIII bicolor will reveal pillar structure. At least 2h total integration recommended."},
    {"name":"NGC7000","full":"NGC 7000 – North America Nebula","ra":"20:58:47","dec":"+44:20","size":120,"mag":4.0,"con":"Cygnus","filter_boost":True,"why":"Enormous emission nebula — the continental shape only appears with a narrowband filter.","tip":"Absolutely needs Ha or UHC filter from suburban sites. Pair with IC 5070 in one shot."},
    {"name":"IC5070","full":"IC 5070 – Pelican Nebula","ra":"20:50:48","dec":"+44:21","size":60,"mag":8.0,"con":"Cygnus","filter_boost":True,"why":"Sits right next to NGC 7000 — both fit in a single wide-field frame.","tip":"Ha filter is essential. The beak region shows intense ionisation fronts."},
    {"name":"NGC6992","full":"NGC 6992 – Eastern Veil Nebula","ra":"20:56:24","dec":"+31:43","size":60,"mag":7.0,"con":"Cygnus","filter_boost":True,"why":"Supernova remnant with intricate filament structure. Glows beautifully in OIII.","tip":"OIII filter is ideal. Combine with NGC 6960 for the full Veil complex."},
    {"name":"M27","full":"M27 – Dumbbell Nebula","ra":"19:59:36","dec":"+22:43","size":15,"mag":7.5,"con":"Vulpecula","filter_boost":True,"why":"Largest and brightest planetary nebula. Visible even from the city without a filter.","tip":"OIII filter dramatically improves contrast. A little focal length helps resolve the shape."},
    {"name":"NGC2237","full":"NGC 2237 – Rosette Nebula","ra":"6:33:45","dec":"+4:59","size":80,"mag":9.0,"con":"Monoceros","filter_boost":True,"why":"Huge and photogenic emission nebula surrounding an open cluster.","tip":"Ha filter is a must. Long integration rewards patience."},
    {"name":"IC434","full":"IC 434 – Horsehead Nebula","ra":"5:40:59","dec":"-2:27","size":8,"mag":6.8,"con":"Orion","filter_boost":True,"why":"Iconic dark nebula silhouetted against a bright emission background.","tip":"Ha filter essential. Frame with the Flame Nebula (NGC 2024) for a dramatic composition."},
    {"name":"NGC1499","full":"NGC 1499 – California Nebula","ra":"4:00:42","dec":"+36:37","size":160,"mag":6.0,"con":"Perseus","filter_boost":True,"why":"One of the largest emission nebulae — only wide-field instruments can capture the whole cloud.","tip":"RedCat-range focal lengths are ideal. Ha filter mandatory from any lit area."},
    {"name":"NGC6888","full":"NGC 6888 – Crescent Nebula","ra":"20:12:07","dec":"+38:21","size":20,"mag":7.4,"con":"Cygnus","filter_boost":True,"why":"Wolf-Rayet stellar bubble with dramatic shell structure. Responds beautifully to Ha and OIII.","tip":"Bicolor Ha+OIII gives a spectacular result."},
    {"name":"M57","full":"M57 – Ring Nebula","ra":"18:53:35","dec":"+33:01","size":3,"mag":8.8,"con":"Lyra","filter_boost":False,"why":"Classic planetary nebula ring. Small but bright — needs at least 500mm focal length to resolve well.","tip":"OIII filter reveals the faint outer halo with enough integration."},
    {"name":"M78","full":"M78 – Reflection Nebula","ra":"5:46:46","dec":"+0:03","size":8,"mag":8.3,"con":"Orion","filter_boost":False,"why":"Brightest reflection nebula, glowing blue around embedded stars.","tip":"No emission-line filter — this is a reflection nebula. Broadband LRGB works best."},
  ],
  "galaxies": [
    {"name":"M31","full":"M31 – Andromeda Galaxy","ra":"0:42:44","dec":"+41:16","size":190,"mag":3.4,"con":"Andromeda","filter_boost":False,"why":"Nearest large galaxy — so large it needs a mosaic or ultra-wide instrument to capture fully.","tip":"The core overexposes quickly; use shorter subs or HDR stacking. Dust lanes shine in RGB."},
    {"name":"M51","full":"M51 – Whirlpool Galaxy","ra":"13:29:53","dec":"+47:12","size":12,"mag":8.4,"con":"CVn","filter_boost":False,"why":"Face-on spiral with companion NGC 5195 — an iconic interacting pair.","tip":"Higher focal length resolves the spiral arms. Aim for 3h+ total integration."},
    {"name":"M81","full":"M81 – Bode's Galaxy","ra":"9:55:33","dec":"+69:04","size":27,"mag":6.9,"con":"Ursa Major","filter_boost":False,"why":"Bright grand-design spiral. Pairs beautifully with M82 in one wide frame.","tip":"Circumpolar from Sofia — accessible all year. 2h brings out the spiral structure."},
    {"name":"M82","full":"M82 – Cigar Galaxy","ra":"9:55:52","dec":"+69:41","size":11,"mag":8.4,"con":"Ursa Major","filter_boost":False,"why":"Edge-on starburst galaxy next to M81. Its Ha filaments are a beautiful bonus.","tip":"Frame M81 and M82 together. Ha filter captures the starburst jets."},
    {"name":"M101","full":"M101 – Pinwheel Galaxy","ra":"14:03:12","dec":"+54:21","size":29,"mag":7.9,"con":"Ursa Major","filter_boost":False,"why":"Large face-on spiral with prominent HII regions. Well-placed for spring from mid-latitudes.","tip":"Low surface brightness — needs dark skies and long integration. 4h+ ideal."},
    {"name":"M33","full":"M33 – Triangulum Galaxy","ra":"1:33:51","dec":"+30:39","size":73,"mag":5.7,"con":"Triangulum","filter_boost":False,"why":"Third largest in the Local Group. Large but low surface brightness.","tip":"Wide-field essential. Ha filter reveals spectacular HII regions including NGC 604."},
    {"name":"M104","full":"M104 – Sombrero Galaxy","ra":"12:39:59","dec":"-11:37","size":9,"mag":8.0,"con":"Virgo","filter_boost":False,"why":"Iconic edge-on galaxy with a massive dust lane. Compact but bright.","tip":"Longer focal lengths (700mm+) bring out the dust lane detail."},
    {"name":"NGC4565","full":"NGC 4565 – Needle Galaxy","ra":"12:36:20","dec":"+25:59","size":16,"mag":9.6,"con":"Coma Ber.","filter_boost":False,"why":"Textbook edge-on spiral with a beautifully thin disk and central bulge.","tip":"Medium focal length (500-800mm) is ideal. Long integration reveals faint dust extensions."},
    {"name":"M64","full":"M64 – Black Eye Galaxy","ra":"12:56:44","dec":"+21:41","size":10,"mag":8.5,"con":"Coma Ber.","filter_boost":False,"why":"Distinctive dark dust lane near the nucleus gives this galaxy its famous look.","tip":"Medium focal length resolves the dust lane clearly."},
    {"name":"NGC891","full":"NGC 891 – Silver Sliver Galaxy","ra":"2:22:33","dec":"+42:21","size":14,"mag":9.9,"con":"Andromeda","filter_boost":False,"why":"Perfect edge-on spiral with a dramatic central dust lane.","tip":"Longer focal length is better. Very faint — 4h+ integration recommended."},
  ],
  "clusters": [
    {"name":"M13","full":"M13 – Great Hercules Cluster","ra":"16:41:41","dec":"+36:28","size":20,"mag":5.8,"con":"Hercules","filter_boost":False,"why":"The finest globular cluster in the northern sky. Fully resolved at moderate focal lengths.","tip":"500-800mm shows individual stars beautifully. No filter needed."},
    {"name":"M92","full":"M92 – Second Hercules Cluster","ra":"17:17:07","dec":"+43:08","size":14,"mag":6.4,"con":"Hercules","filter_boost":False,"why":"Often overlooked next to M13 but stunning in its own right.","tip":"Pair with M13 in one frame at ~250mm for a striking two-globular composition."},
    {"name":"M3","full":"M3 – Great CVn Globular","ra":"13:42:11","dec":"+28:23","size":18,"mag":6.2,"con":"CVn","filter_boost":False,"why":"One of the largest and brightest globulars, with a beautiful dense core.","tip":"Well-resolved at 500mm+. Spring's best globular cluster target."},
    {"name":"M5","full":"M5 – Serpens Globular Cluster","ra":"15:18:34","dec":"+2:05","size":23,"mag":5.6,"con":"Serpens","filter_boost":False,"why":"Rivals M13 in brightness and beauty. Rich star field and well-resolved halo.","tip":"Often underappreciated — compare with M13 for a fun imaging project."},
    {"name":"M4","full":"M4 – Scorpius Globular Cluster","ra":"16:23:35","dec":"-26:32","size":36,"mag":5.4,"con":"Scorpius","filter_boost":False,"why":"One of the closest globulars to Earth. Loose structure with a distinctive bar of stars.","tip":"Low from mid-latitudes — image when highest. Wide field shows its loose texture."},
    {"name":"NGC869","full":"NGC 869/884 – Double Cluster","ra":"2:20:00","dec":"+57:08","size":60,"mag":4.3,"con":"Perseus","filter_boost":False,"why":"Two rich open clusters side by side — one of the most stunning wide-field targets in the sky.","tip":"Perfect at 200-400mm. Circumpolar from Bulgaria — accessible all year."},
    {"name":"M45","full":"M45 – Pleiades","ra":"3:47:24","dec":"+24:07","size":110,"mag":1.6,"con":"Taurus","filter_boost":False,"why":"The most famous open cluster. Blue reflection nebulosity around the stars is a beautiful bonus.","tip":"Very wide field needed (150-300mm). Longer exposure brings out the blue nebulosity."},
    {"name":"Mel111","full":"Mel 111 – Coma Berenices Cluster","ra":"12:25:06","dec":"+26:06","size":275,"mag":1.8,"con":"Coma Ber.","filter_boost":False,"why":"Enormous naked-eye cluster — only very short focal lengths (under 300mm) can frame it entirely.","tip":"One of those targets where RedCat-style wide-angle instruments shine."},
    {"name":"M35","full":"M35 + NGC 2158 – Gemini Clusters","ra":"6:08:54","dec":"+24:20","size":28,"mag":5.3,"con":"Gemini","filter_boost":False,"why":"Foreground open cluster with a compressed background cluster — great depth-of-field visual effect.","tip":"Medium focal length (400-600mm) resolves both clusters together beautifully."},
    {"name":"M11","full":"M11 – Wild Duck Cluster","ra":"18:51:06","dec":"-6:16","size":14,"mag":5.8,"con":"Scutum","filter_boost":False,"why":"Extremely rich open cluster — one of the densest in the Milky Way.","tip":"Medium focal length brings out the fan-shaped richness. No filter needed."},
  ],
}

EQUIPMENT = {
    "RedCat 51 (250mm f/4.9)": 250,
    "Refractor 80mm ED (480mm f/6)": 480,
    "Refractor 80mm (600mm f/7.5)": 600,
    "Refractor 102mm (714mm f/7)": 714,
    "Newtonian 150mm (750mm f/5)": 750,
    'SCT 8" (2032mm f/10)': 2032,
    "Dobsonian 10\" (1200mm f/4.7)": 1200,
    "Custom": None,
}

def get_altitude(ra, dec, lat, lon):
    dt = datetime.now(timezone.utc)
    obs = ephem.Observer()
    obs.lat, obs.lon = str(lat), str(lon)
    obs.elevation = 600
    obs.date = dt.strftime("%Y/%m/%d %H:%M:%S")
    obs.pressure = 0
    b = ephem.FixedBody()
    b._ra = ephem.hours(ra)
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

def score_obj(obj, lat, lon, focal_mm, moon_pct, has_filter):
    alt = get_altitude(obj["ra"], obj["dec"], lat, lon)
    if alt < 15:
        return None, alt
    if alt >= 45:
        a = min(100, 55 + (alt - 45) * 0.8)
    else:
        a = (alt - 15) / 30 * 55
    fill = fov_fill(obj["size"], focal_mm)
    if 8 <= fill <= 70:
        f = 100
    elif fill < 8:
        f = max(0, fill / 8 * 60)
    else:
        f = max(30, 100 - (fill - 70) * 0.8)
    penalty = (moon_pct / 100) * 30
    if has_filter and obj["filter_boost"]:
        penalty *= 0.25
    return round(a * 0.5 + f * 0.4 - penalty, 1), round(alt, 1)

def get_difficulty(obj, focal_mm, moon_pct, has_filter):
    fill = fov_fill(obj["size"], focal_mm)
    if obj["mag"] > 9.5 or (moon_pct > 50 and not (has_filter and obj["filter_boost"])):
        return "Advanced", "#c84040"
    if obj["mag"] > 7.5 or fill < 5 or fill > 80:
        return "Intermediate", "#c8a020"
    return "Beginner", "#3a9e5f"

def build_why(obj, alt, focal_mm, moon_pct, has_filter):
    parts = [obj["why"]]
    if alt >= 60:
        parts.append(f"Excellent altitude at {alt:.0f}° tonight — minimal atmospheric distortion.")
    elif alt >= 35:
        parts.append(f"Good altitude at {alt:.0f}° — solid imaging window.")
    else:
        parts.append(f"Low at {alt:.0f}° — image during the brief transit window.")
    fill = fov_fill(obj["size"], focal_mm)
    if fill < 5:
        parts.append(f"Small for this focal length ({fill:.0f}% frame fill) — consider a Barlow.")
    elif fill > 75:
        parts.append(f"Large object ({fill:.0f}% frame fill) — mosaic or shorter focal length needed.")
    else:
        parts.append(f"Great FOV fit at {fill:.0f}% frame fill.")
    if moon_pct > 60 and obj["filter_boost"]:
        if has_filter:
            parts.append("Bright moon tonight — your narrowband filter will save this shot.")
        else:
            parts.append(f"Moon at {moon_pct:.0f}% — a narrowband filter would help significantly.")
    return " ".join(parts)

# ── UI ─────────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">✦ AstroAdvisor</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">DEEP SKY TARGET PLANNER · NO API KEY NEEDED</div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 📍 Location")
    lat = st.number_input("Latitude",  value=42.62, format="%.4f", step=0.01)
    lon = st.number_input("Longitude", value=23.23, format="%.4f", step=0.01)
    st.caption("Default: Vladaya / Sofia")
    st.markdown("---")
    st.markdown("### 🔭 Equipment")
    scope = st.selectbox("Telescope / Lens", list(EQUIPMENT.keys()))
    focal_mm = EQUIPMENT[scope]
    if focal_mm is None:
        focal_mm = st.number_input("Focal length (mm)", value=500, min_value=50, max_value=5000)
    has_filter = st.checkbox("I have a narrowband / UHC filter", value=True)
    st.markdown("---")
    st.markdown("### 🎯 Target types")
    want_neb = st.checkbox("Nebulae",  value=True)
    want_gal = st.checkbox("Galaxies", value=True)
    want_clu = st.checkbox("Clusters", value=True)
    run = st.button("▶  FIND MY TARGETS", use_container_width=True)

moon_pct = moon_phase()
now_utc = datetime.now(timezone.utc)
c1,c2,c3,c4 = st.columns(4)
c1.metric("🌙 Moon",  f"{moon_pct:.0f}%")
c2.metric("📅 Date",  now_utc.strftime("%d %b %Y"))
c3.metric("🕐 UTC",   now_utc.strftime("%H:%M"))
c4.metric("🔭 Focal", f"{focal_mm} mm")
st.markdown("---")

if not run:
    st.markdown("""<div style="text-align:center;padding:3rem 1rem;color:#2a4a7a;
    font-family:'Space Mono',monospace;font-size:0.85rem;letter-spacing:1px;">
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

with st.spinner("Computing sky positions..."):
    for ttype in types_wanted:
        scored = []
        for obj in DSO[ttype]:
            s, alt = score_obj(obj, lat, lon, focal_mm, moon_pct, has_filter)
            if s is not None:
                scored.append({**obj, "_score": s, "_alt": alt})
        scored.sort(key=lambda x: x["_score"], reverse=True)
        top5 = scored[:5]

        st.markdown(f'<div class="section-header">{ICONS[ttype]} {LABELS[ttype]} — TOP {len(top5)}</div>', unsafe_allow_html=True)
        if not top5:
            st.markdown('<div class="warn-box">No objects above the horizon right now.</div>', unsafe_allow_html=True)
            continue

        for i, obj in enumerate(top5):
            dlabel, dcolor = get_difficulty(obj, focal_mm, moon_pct, has_filter)
            fill = fov_fill(obj["size"], focal_mm)
            why  = build_why(obj, obj["_alt"], focal_mm, moon_pct, has_filter)
            st.markdown(f"""
            <div class="target-card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                  <div class="card-title">#{i+1} &nbsp; {obj['full']}</div>
                  <div class="card-type">{ttype[:-1].upper()} &nbsp;·&nbsp; {obj['con']}</div>
                </div>
                <div style="font-family:'Space Mono',monospace;font-size:0.72rem;color:{dcolor};
                            border:1px solid {dcolor}44;border-radius:20px;padding:2px 10px;white-space:nowrap;">
                  {dlabel}
                </div>
              </div>
              <div class="card-desc">{why}</div>
              <div class="card-tip">💡 {obj['tip']}</div>
              <div class="card-meta">
                <span class="meta-pill">Alt {obj['_alt']}°</span>
                <span class="meta-pill">Score {obj['_score']}</span>
                <span class="meta-pill">{fill:.0f}% frame fill</span>
                <span class="meta-pill">Mag {obj['mag']}</span>
                {'<span class="meta-pill">🔴 Filter helps</span>' if obj["filter_boost"] else ''}
              </div>
            </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"""<div style="font-family:'Space Mono',monospace;font-size:0.72rem;color:#1e3a5f;text-align:center;padding:0.5rem;">
UTC {now_utc.strftime('%Y-%m-%d %H:%M')} · Moon {moon_pct:.0f}% · Focal {focal_mm}mm · {'Narrowband ✓' if has_filter else 'Broadband only'}
</div>""", unsafe_allow_html=True)
