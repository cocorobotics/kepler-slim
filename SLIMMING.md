# Slimming kepler.gl for Hex (10 MB web-view limit)

Goal: get the kepler.gl UMD bundle (`umd/keplergl.min.js`) small enough to load inside a
Hex (app.hex.tech) web view, which rejects assets larger than **10 MB**.

This document records what actually drives the bundle size, what does and does not help,
and a concrete path to a working slim build. All numbers are **measured** on this repo at
version `3.3.0-alpha.1` using esbuild's metafile (see `esbuild/analyze.mjs`).

## TL;DR

| Build | Raw `.js` | gzip | Under 10 MB? |
|---|---|---|---|
| Baseline (current `build:umd`) | **14.15 MB** | 3.84 MB | ❌ |
| – AI Assistant | **10.16 MB** | 2.66 MB | ❌ (barely over) |
| – AI Assistant – mapbox-gl (maplibre basemaps only) | **8.65 MB** | ~1.8 MB | ✅ |

- **Removing DuckDB does nothing.** `@kepler.gl/duckdb` is a separate, opt-in workspace that
  is *not* imported by `src/index.js` (the UMD entry) or by any bundled package. It is not in
  the default bundle, so removing it saves **0 MB**. (Its heavy deps — `monaco-editor`,
  `@duckdb/duckdb-wasm`, `apache-arrow` — only ship if an app explicitly imports
  `@kepler.gl/duckdb`.)
- **The single biggest contributor is the AI Assistant (≈3.77 MB, 26.6%)** — bigger than the
  entire deck.gl / luma.gl / loaders.gl rendering core. It is pulled in by exactly one line in
  `src/index.js` and nothing else imports it, so it is the cleanest large win.
- **Compression is not the lever.** The full 14 MB bundle gzips to 3.84 MB. If Hex's 10 MB
  limit applied to the *transferred* (gzipped) size, the stock bundle would already load. It
  doesn't, so the limit is on the **raw/uncompressed file** — we must physically shrink it.

## Where the 14.15 MB goes (by ecosystem)

Measured from the esbuild metafile, grouped by dependency family:

| Bytes | % | Group |
|---|---|---|
| 3.77 MB | 26.6% | **AI Assistant** ecosystem (echarts, zrender, `@openassistant/*`, `@ai-sdk/*`, `@geoda/*`, framer-motion, @heroui, @react-aria, html2canvas, openai, zod, jsts) |
| 1.95 MB | 13.8% | kepler.gl's own source |
| 1.79 MB | 12.7% | Rendering core: `@deck.gl/*`, `@luma.gl/*`, `@loaders.gl/*`, `@math.gl/*`, geoarrow |
| 1.58 MB | 11.2% | Long tail (everything else) |
| 1.49 MB | 10.6% | **mapbox-gl** (basemap renderer #1) |
| 0.81 MB | 5.7% | moment + moment-timezone |
| 0.80 MB | 5.7% | **maplibre-gl** (basemap renderer #2 — both are bundled) |
| 0.58 MB | 4.1% | apache-arrow |
| 0.44 MB | 3.1% | charts: react-vis / d3 |
| 0.34 MB | 2.4% | h3-js |
| 0.31 MB | 2.2% | misc React UI widgets (react-virtualized, react-color, date/time pickers, modal, tooltip) |
| 0.14 MB | 1.0% | lexical (rich-text editor) |
| 0.07 MB | 0.5% | turf |

Top single packages: `mapbox-gl` 1.49 MB, `echarts` 0.80 MB, `maplibre-gl` 0.78 MB,
`moment-timezone` 0.75 MB, `apache-arrow` 0.56 MB, `h3-js` 0.34 MB.

There is no single dominant chunk after the AI assistant — it's a long tail, so getting well
under 10 MB means stacking a few removals.

## Recommended path

### Step 1 — Remove the AI Assistant (clean, ~4 MB, 1-line change)

Nothing in the core imports it; it is exposed only via `src/index.js`:

```js
// src/index.js
export * from '@kepler.gl/ai-assistant';   // <-- delete this line for the slim build
```

Result: **10.16 MB**. This alone is *just* over the limit (10.16 MiB > 10 MiB), so pair it
with Step 2.

### Step 2 — Ship one basemap renderer, not two (~1.5 MB)

The bundle currently includes **both** `mapbox-gl` (1.13.1, 1.49 MB) and `maplibre-gl`
(4.x, 0.78 MB). kepler.gl 3.x defaults to free maplibre/Carto basemaps. If the Hex use case
does not need Mapbox-hosted styles (which require a Mapbox token anyway), drop `mapbox-gl`.

Stubbing `mapbox-gl` at bundle time (verified to build cleanly) yields **8.65 MB** — a
comfortable margin. This requires either a build-time alias of `mapbox-gl` to an empty module
or small source edits where `mapbox-gl` is imported in `@kepler.gl/components`; it is more
involved than Step 1 and must be validated at runtime with the basemaps you actually use.

### Further optional trims (if you want more headroom)

- `moment` + `moment-timezone` → 0.81 MB (used by time filters; replacing with date-fns/dayjs
  is a larger refactor).
- `react-vis` charts → 0.44 MB (used by the time-series filter plot).
- `lexical` rich-text editor → 0.14 MB (map annotations).
- `h3-js` → 0.34 MB (only needed for the H3 hexbin layer).

## How to reproduce / analyze

`esbuild/analyze.mjs` builds the UMD bundle exactly like `build:umd` but (a) emits an esbuild
metafile next to the output and (b) supports stubbing packages via `KEPLER_EXCLUDE` to measure
"what if we removed X" without touching source.

```bash
# one-time: install workspace deps and wire packages to source
corepack enable && corepack prepare yarn@4.4.0 --activate
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true yarn install
yarn workspaces foreach -At run stab

# baseline build + metafile
node ./esbuild/analyze.mjs            # -> umd/keplergl.analyze.js + .meta.json

# measure a hypothetical removal (comma-separated package names)
KEPLER_EXCLUDE="@kepler.gl/ai-assistant" KEPLER_OUT=./umd/slim.js node ./esbuild/analyze.mjs
```

Note: this repo targets Node 20.19.3 (`.nvmrc`). `analyze.mjs` reads `package.json` via `fs`
(rather than an import-assertion) so it also runs on newer Node versions.

## Open question for the Hex integration

Confirm what Hex's 10 MB limit measures:
- If it's the **raw hosted file**: Steps 1 + 2 (→ 8.65 MB) are the fix.
- If it's the **gzipped transfer**: the stock bundle (gzip 3.84 MB) already fits — the load
  failure would be something else (e.g. Hex not serving `Content-Encoding: gzip`, or a
  per-request size cap before decompression).

The evidence (stock gzip = 3.84 MB but it still fails) points to a raw-file limit.
