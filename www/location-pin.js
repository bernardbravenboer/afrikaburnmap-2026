// ============================================================
// AfrikaBurn 2026 — GPS Location Pin
// Supports two map images:
//   - afrikaburn2026_landscape.png (6372x3554) — APK full res
//   - afrikaburn2026_web.jpg       (3186x1777) — web 50% version
// ============================================================

// Detect which image is loaded and set transform accordingly
const mapImg = document.getElementById("mapimg");
const imgSrc = mapImg ? mapImg.getAttribute("src") : "";
const isWebVersion = imgSrc.includes("web");

// Scale factor between full-res and web version
const IMG_SCALE = isWebVersion ? 0.5 : 1.0;

// GPS -> full-res landscape pixel transform
// (web version pixels = full-res pixels * 0.5)
function gpsToPixel(lat, lng) {
  const px = (246888.0115 * lng + 33090.7829  * lat + -3848409.1232) * IMG_SCALE;
  const py = ( 35751.3259 * lng + -246189.0256 * lat + -8716423.0033) * IMG_SCALE;
  return { x: px, y: py };
}

const IMG_W = 6372 * IMG_SCALE;
const IMG_H = 3554 * IMG_SCALE;

// px/metre: landscape image ~6372px covers ~1.13 degrees longitude
// ~6372 / (1.13 * 91000m) ~= 0.062 px/m at full res
const PX_PER_METRE = (6372 / (1.13 * 91000)) * IMG_SCALE;

// ── Create the location pin element ────────────────────────
const locPin = document.createElement("div");
locPin.id = "loc-pin";
locPin.style.cssText = `
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #2196F3;
  border: 3px solid #fff;
  box-shadow: 0 0 0 2px #2196F3, 0 0 12px rgba(33,150,243,0.8);
  transform: translate(-50%, -50%);
  z-index: 50;
  display: none;
  pointer-events: none;
`;

const locRing = document.createElement("div");
locRing.id = "loc-ring";
locRing.style.cssText = `
  position: absolute;
  border-radius: 50%;
  background: rgba(33,150,243,0.15);
  border: 1.5px solid rgba(33,150,243,0.5);
  transform: translate(-50%, -50%);
  z-index: 49;
  display: none;
  pointer-events: none;
`;

const mapDiv = document.getElementById("map");
mapDiv.appendChild(locRing);
mapDiv.appendChild(locPin);

// ── Find me button ──────────────────────────────────────────
const locBtn = document.createElement("button");
locBtn.id = "loc-btn";
locBtn.title = "Show my location";
locBtn.textContent = "\u2295";
locBtn.style.cssText = `
  position: absolute;
  top: 172px;
  right: 12px;
  z-index: 20;
  width: 32px;
  height: 32px;
  background: #1a1a1a;
  color: #eee;
  border: 1px solid #333;
  border-radius: 6px;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,.3);
  display: flex;
  align-items: center;
  justify-content: center;
`;
locBtn.addEventListener("mouseover", () => locBtn.style.background = "#2a2a2a");
locBtn.addEventListener("mouseout",  () => locBtn.style.background = "#1a1a1a");
document.body.appendChild(locBtn);

// ── GPS state ───────────────────────────────────────────────
let watchId = null;
let locActive = false;

function updatePin(lat, lng, accuracyMetres) {
  const { x, y } = gpsToPixel(lat, lng);

  if (x < 0 || x > IMG_W || y < 0 || y > IMG_H) {
    locPin.style.display = "none";
    locRing.style.display = "none";
    locBtn.style.color = "#888";
    locBtn.title = "You are outside the map area";
    return;
  }

  locPin.style.left = x + "px";
  locPin.style.top  = y + "px";
  locPin.style.display = "block";

  const ringR = Math.max(10, accuracyMetres * PX_PER_METRE);
  locRing.style.left   = x + "px";
  locRing.style.top    = y + "px";
  locRing.style.width  = (ringR * 2) + "px";
  locRing.style.height = (ringR * 2) + "px";
  locRing.style.display = "block";

  locBtn.style.color = "#2196F3";
  locBtn.title = "Accuracy: \xb1" + Math.round(accuracyMetres) + "m";
}

function startTracking() {
  if (!("geolocation" in navigator)) {
    alert("Geolocation is not available on this device.");
    return;
  }
  locActive = true;
  locBtn.style.color = "#2196F3";

  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      updatePin(pos.coords.latitude, pos.coords.longitude, pos.coords.accuracy);
    },
    (err) => {
      console.warn("Geolocation error:", err.message);
      locBtn.style.color = "#ff3d8a";
      locBtn.title = "Location unavailable";
    },
    { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
  );
}

function stopTracking() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
  locActive = false;
  locPin.style.display = "none";
  locRing.style.display = "none";
  locBtn.style.color = "#eee";
  locBtn.title = "Show my location";
}

locBtn.addEventListener("click", () => {
  if (locActive) stopTracking();
  else startTracking();
});
