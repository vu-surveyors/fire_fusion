# FireFusion — Desktop Prototype: What Changed (Original → Current)

Reference for every difference between the original desktop HTML the team provided and the reworked desktop web app delivered after the build-out and audit. Single-file, self-contained app in both versions (all CSS/JS/assets inline, no external network requests at runtime).

---

## 1. Branding & logo

- **Original:** Header brand was an inline SVG flame drawing plus the word-mark text. No raster assets existed anywhere in the file; no favicon.
- **Changed:** Brand is now a button that links to the Overview screen. It shows the FireFusion logo embedded as a data-URI PNG (harmonized brand master), with a warm orange glow. The button carries an accessible label (e.g. "FireFusion — go to Overview") and the logo image has descriptive alt text.
- **Added:** data-URI SVG favicon in the document head, matching the logo.
- **Embedded assets overall:** the file now embeds PNG/WebP/SVG data URIs (logo, favicon, map basemap). The original embedded only font files.

## 2. Map screen — full replacement

- **Original:** A lightweight inline SVG map with simple pan/zoom. The pan/zoom behavior lived in a few small helper functions and in map-specific state fields on the app state (e.g. zoom, panX/panY, mapDetail, mapSource).
- **Changed:** The entire map screen was replaced with the full EMBER Detection Map application embedded as a self-contained document inside an `<iframe>` (via `srcdoc`). This single-file embed includes:
  - Interactive topographic basemap of the Sundarbans (embedded WebP imagery).
  - MODIS/VIIRS cluster markers with confidence tiers, FRP values, counts, and cluster outlines labeled as illustrative groupings.
  - Full interaction model: zoom (wheel, buttons, pinch), pan (drag), double-tap/double-click zoom, keyboard navigation, search with results, collapsible glass "Layers & filters" drawer, Overview summary card, detection details view.
  - Its own design system, self-hosted web fonts (woff2), and a backend integration seam: `window.FireMapPrototype.setData({ clusters, observations, updatedAt })` applies an external payload; `resetDemo()` restores sample data; `setLoading/setError` drive status banners.
  - No external tile servers, CDNs, or font downloads.
  - The iframe carries a descriptive `title` for screen readers.
- **Removed:** the three small map interaction helper functions and all map-pan/zoom state fields from the shell. Map behavior now lives entirely inside the embedded app.

## 3. Calendar — every day is selectable, plus accessibility rewrite

- **Original:** Only days with a data record were interactive buttons; non-record days were inert `<span>` elements (not focusable, not selectable). Users could not explore "empty" days.
- **Changed:** Every day in the month grid is now a real `<button>` (including non-record days), with:
  - `aria-pressed` on the selected day.
  - Screen-reader-only (`sr-only`) labels describing each day (date + record count / "no records available" / "future date").
  - Recordless dates selectable end-to-end; the "Selected day details" panel shows a proper "no records" empty state instead of failing.
  - The activity-density legend control now carries a screen-reader-only label.
- **Date modal:** if the selected date has no record, the quick-pick list still shows it as the selected row (it used to vanish from the list entirely).
- **New date helpers:** `isISODate` (strict shape/calendar validation), `dateLabel` (formatted labels), `normDate` (numeric normalization of record fields).

## 4. Overview screen

- **Original:** The hero pill showed a hardcoded date ("15 Mar · Asia/Dhaka") regardless of the selected date.
- **Changed:** The pill renders the currently selected date, escaped, e.g. "12 Mar 2026 · Asia/Dhaka".

## 5. Data validation & fault tolerance

- **Original:** The selected-date lookup returned the raw record or `undefined` (downstream code could crash or misrender on missing/recordless dates and unnormalized numbers).
- **Changed:**
  - The selected-date lookup always returns a usable object: the normalized record if one exists, otherwise a synthesized `{ ok: false, label: … }` fallback — screens never crash.
  - Cluster records are coerced to numbers (`frp`, `modis`, `viirs`, `raw`) at read time; date records' `raw`/`harm`/`int` interval are normalized.
  - Any backend payload that produces missing dates, unknown months, or malformed numbers degrades to empty states instead of breaking.
  - All user-injectable strings are HTML-escaped before rendering (including peak-day insight and date labels).
  - URL hash parsing strictly validates the `date` parameter and clamps the `month` parameter with a last-month fallback.

## 6. Full-viewport chrome (no floating card, no gutters)

- **Original:** At most widths the app rendered as a floating, rounded "phone" card (≈360–390 px wide, ~34 px corner radius, border, large drop shadow) over a visible purple/teal radial-gradient backdrop. On shorter desktop viewports it was a capped 1480 px card with a 14 px page gutter, same backdrop glows.
- **Changed:**
  - The page backdrop is a single flat `--bg` (#080d0f) at every width — no glows, no gutters, no frame, no shadow, no border, no corner radius.
  - The app always fills the viewport edge-to-edge (`100%` × `100dvh`), phone through ultrawide.
  - Ultrawide displays are no longer capped or padded.
  - Mid-range widths (601–979 px) use a centered content column (`max-width: 1080 px`) with the chrome (header/nav) full-width.
  - Desktop's internal grid layout (sidebar navigation, split content panes) is unchanged.

## 7. Selected-day panel update behavior

- **Original:** When switching dates, the "Selected day details" panel replayed an update animation that faded it from ~45 % opacity, nudged it vertically, and pulsed a shadow — a visible flash/jitter on every date switch.
- **Changed:** The update animation no longer touches opacity or transforms. It is a single 260 ms fade of a thin cyan halo ring (box-shadow only). The panel changes content without flashing; `prefers-reduced-motion` is honored automatically.

## 8. Compact density mode (broken → working)

- **Original:** All 11 compact-density CSS rules had escaped attribute quotes (`data-density=\"compact\"`), so no rule ever matched: the density toggle was a dead control.
- **Changed:** The escaped quotes were removed from all compact-density rules; the comfort/compact toggle now works as designed (compact ≈120 px metric height, tighter internal padding).

## 9. Dead code removed

- Legacy map-workspace rule blocks left over from earlier iterations (superseded by the embedded map).
- Exact-duplicate CSS rule blocks.
- Unused design tokens (e.g. legacy panel/type/leading variables).
- The unused `mode-in` `@keyframes`.
- Main-document CSS reduced from ~266 KB to ~257 KB.

## 10. What did NOT change

- Document title, character encoding, viewport meta tag.
- Sample dataset (dates, clusters, methods copy) and the MODIS→VIIRS handover narrative.
- CAL_MONTHS (March/February/January 2026), hash-based routing (`#view=…&date=…`), and the 6 screens: Overview, Map, Calendar, Records/evidence, Validation, Methods.
- Validation, Records and Methods screen implementations (function-identical), `head()`, `say()`, `reset()` helpers.
- Comfortable/compact density toggle UI and its `localStorage` persistence.
- All screens' language: English, Asia/Dhaka time zone context.

---

*Current deliverable: `FireFusion_Desktop_Prototype.html` — a single self-contained HTML file (open directly in any browser; no server, network, or build step required).*
