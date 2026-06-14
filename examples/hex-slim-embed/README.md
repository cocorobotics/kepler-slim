# Embedding the slim build in Hex (Python)

Render a kepler.gl map inside a [Hex](https://app.hex.tech) Python cell using the
**slim** UMD build from this repo's releases. Hex rejects web-view assets larger
than 10 MB; the stock kepler.gl bundle is ~14 MB, while the slim build is ~9.8 MB
(see [`SLIMMING.md`](../../SLIMMING.md)).

[`kepler_hex.py`](./kepler_hex.py) is fully self-contained: it does **not** install
or import the `keplergl` PyPI package. The only kepler asset loaded is the slim
release URL; React/Redux/styled-components come from unpkg as the bundle's
externals. A built-in assertion guarantees no generic `unpkg.com/kepler.gl`
bundle can sneak in.

## Requirements

- **A Mapbox access token.** The slim build dropped the MapLibre renderer, so the
  basemap defaults to Mapbox `dark`. Use the Mapbox styles (`dark`, `light`,
  `muted`, `satellite`); the free Carto/MapLibre styles won't render.
- `pandas` (already present in Hex) for plain lat/lon DataFrames. `geopandas` only
  if you pass GeoDataFrames.

## Use in Hex

Add `kepler_hex.py` to your Hex project (upload it, or paste its contents into a
cell), then:

```python
import pandas as pd
from kepler_hex import render

# swap in your real (e.g. SQL-cell) dataframe — lat/lon columns are auto-detected
df = pd.DataFrame({
    "lat": [37.77, 40.71, 34.05],
    "lng": [-122.42, -74.01, -118.24],
    "city": ["SF", "NYC", "LA"],
})

render({"my_data": df}, mapbox_token="pk.your_mapbox_token", height=700)
```

`render(...)` returns an `IPython.display.IFrame` — make it the last expression
in the cell so Hex displays it. It loads the map as a `data:` URL via the
iframe's `src` (not `srcdoc`), so the frame is its own browsing context and
kepler's scripts run instead of being blocked by Hex's page CSP.

## Troubleshooting

- **Totally blank (no kepler UI at all):** the map scripts were blocked. Make
  sure you're on the current `render()` (it uses `IFrame` + a `data:` src, not
  `HTML(srcdoc=…)`). A `srcdoc` iframe inherits Hex's restrictive CSP and renders
  empty. If it's still blank, Hex's CSP is blocking embedded scripts entirely —
  host the output of `kepler_html(...)` at a public URL and load it with
  `IPython.display.IFrame(src=that_url)`.
- **Kepler UI loads but the map area is blank:** that's the Mapbox token — you
  left the `pk.your_mapbox_token` placeholder, or the token is invalid/lacks
  permissions. The slim build has no free fallback basemap.

### Options

- `read_only=True` — hide the side panel for a display-only map.
- `config={...}` — pass a saved kepler.gl config dict to reproduce a styled map.
- `center_map=True` (default) — fit the map bounds to the data on load.
- `release=...` — point at a different slim release tag.
- GeoData: pass a `GeoDataFrame` or a GeoJSON `dict` instead of a DataFrame to use
  the GeoJSON path.

If you need the raw HTML string (e.g. to write to a file), call
`kepler_hex.kepler_html(...)` directly.

## Why not the `keplergl` package?

The `keplergl` PyPI package is only an HTML generator — in its `save_to_html`
path it never supplies the map's JavaScript, just a `<script src>` pointing at a
CDN. Whether you get the full or slim build is decided entirely by that URL. This
example skips the package and pins the URL to the slim release directly, so the
generic bundle is never in play.
