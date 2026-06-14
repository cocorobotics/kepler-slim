# SPDX-License-Identifier: MIT
# Copyright contributors to the kepler.gl project
"""Embed the kepler-slim UMD build inside a Hex (app.hex.tech) Python cell.

Hex rejects web-view assets larger than 10 MB, which the stock ~14 MB kepler.gl
UMD bundle exceeds. This helper renders a kepler.gl map by loading the slim
(~9.8 MB) bundle published at github.com/cocorobotics/kepler-slim/releases.

It is fully self-contained: it does NOT install or import the `keplergl` PyPI
package. The only kepler asset loaded is the slim release URL below; React /
Redux / styled-components are loaded from unpkg as the bundle's externals. The
HTML bootstrap mirrors kepler.gl's own standalone template.

Usage (in a Hex Python cell)::

    import pandas as pd
    from kepler_hex import render

    df = pd.DataFrame({"lat": [37.77], "lng": [-122.42], "city": ["SF"]})
    render({"my_data": df}, mapbox_token="pk.your_token")   # last expr in the cell

`pandas` is enough for plain lat/lon DataFrames. Pass GeoDataFrames or GeoJSON
dicts to use the GeoJSON path (requires `geopandas` for GeoDataFrames).

NOTE: the slim build dropped the MapLibre renderer, so a Mapbox access token is
REQUIRED and the basemap defaults to Mapbox "dark". Use the Mapbox styles
(dark / light / muted / satellite); the free Carto/MapLibre styles won't render.
"""

from __future__ import annotations

import html as _html
import json
from typing import Any, Dict, Optional

# Rolling LATEST release — always serves the newest slim build. Pin to a tagged
# release (e.g. .../releases/download/v3.3.0-alpha.1-slim.3) for reproducibility.
RELEASE = "https://github.com/cocorobotics/kepler-slim/releases/download/LATEST"

_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8"/>
    <title>__APP_NAME__</title>
    <link rel="stylesheet" href="https://d1a3f4spazzrp4.cloudfront.net/kepler.gl/uber-fonts/4.0.0/superfine.css">
    <link href="__SLIM_CSS__" rel="stylesheet">
    <link href="https://api.tiles.mapbox.com/mapbox-gl-js/v1.1.1/mapbox-gl.css" rel="stylesheet">
    <script src="https://unpkg.com/react@18.3.1/umd/react.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js" crossorigin></script>
    <script src="https://unpkg.com/redux@4.2.1/dist/redux.js" crossorigin></script>
    <script src="https://unpkg.com/react-redux@8.1.2/dist/react-redux.min.js" crossorigin></script>
    <script src="https://unpkg.com/styled-components@6.1.8/dist/styled-components.min.js" crossorigin></script>
    <script src="__SLIM_JS__"></script>
    <style type="text/css">body {margin:0;padding:0;overflow:hidden;}</style>
    <script>const MAPBOX_TOKEN = __MAPBOX_TOKEN__;</script>
  </head>
  <body>
    <div id="app"></div>
__CONFIG_TOOL_HTML__
    <script>
      const reducers = (function (redux, keplerGl) {
        return redux.combineReducers({
          keplerGl: keplerGl.keplerGlReducer.initialState({
            uiState: { readOnly: __READ_ONLY__, currentModal: null }
          })
        });
      }(Redux, KeplerGl));
      const store = Redux.createStore(
        reducers, {}, Redux.compose(Redux.applyMiddleware(...KeplerGl.enhanceReduxMiddleware([])))
      );
      var KeplerElement = (function (react, keplerGl, mapboxToken) {
        return function App() {
          var s = react.useState({width: window.innerWidth, height: window.innerHeight});
          react.useEffect(function () {
            function onResize(){ s[1]({width: window.innerWidth, height: window.innerHeight}); }
            window.addEventListener('resize', onResize);
            return function(){ window.removeEventListener('resize', onResize); };
          }, []);
          return react.createElement('div',
            {style: {position:'absolute', left:0, width:'100vw', height:'100vh'}},
            react.createElement(keplerGl.KeplerGl,
              {mapboxApiAccessToken: mapboxToken, id:'map', width:s[0].width, height:s[0].height}));
        };
      }(React, KeplerGl, MAPBOX_TOKEN));
      ReactDOM.createRoot(document.getElementById('app')).render(
        React.createElement(ReactRedux.Provider, {store}, React.createElement(KeplerElement, null))
      );
      (function (keplerGl, store) {
        var datasets = [];
__DATASETS__
        var config = __CONFIG__;
        window.setTimeout(function () {
          store.dispatch(keplerGl.addDataToMap(
            {datasets: datasets, config: config, options: {centerMap: __CENTER_MAP__}}));
        }, 500);
        var _btn = document.getElementById('kg-cfg-btn');
        if (_btn) _btn.onclick = function () {
          var saved = keplerGl.KeplerGlSchema.getConfigToSave(store.getState().keplerGl.map);
          var _ta = document.getElementById('kg-cfg-out');
          _ta.value = JSON.stringify(saved);
          _ta.style.display = 'block';
          _ta.focus(); _ta.select();
          try {
            document.execCommand('copy');
            _btn.textContent = 'Copied! (paste into Python)';
            setTimeout(function () { _btn.textContent = 'Copy config'; }, 2000);
          } catch (e) {}
        };
      }(KeplerGl, store));
    </script>
  </body>
</html>"""


_CONFIG_TOOL_HTML = """    <div style="position:absolute;top:10px;right:10px;z-index:9999;font-family:sans-serif">
      <button id="kg-cfg-btn" style="padding:6px 10px;cursor:pointer;border-radius:4px;border:1px solid #888;background:#fff">Copy config</button>
      <textarea id="kg-cfg-out" readonly style="display:none;width:380px;height:240px;margin-top:6px;font:11px/1.4 monospace"></textarea>
    </div>"""


def kepler_html(
    datasets: Dict[str, Any],
    config: Optional[dict] = None,
    mapbox_token: str = "",
    center_map: bool = True,
    read_only: bool = False,
    app_name: str = "kepler.gl",
    show_config_tool: bool = True,
    release: str = RELEASE,
) -> str:
    """Return a standalone HTML document that renders a kepler.gl map.

    Args:
        datasets: Mapping of dataset name -> data. Each value may be a
            pandas DataFrame (lat/lon columns auto-detected), a GeoDataFrame,
            a GeoJSON dict, or a raw CSV string.
        config: Optional kepler.gl config dict to reproduce a styled map.
        mapbox_token: Mapbox access token (required for basemaps).
        center_map: Fit the map bounds to the data on load.
        read_only: Hide the side panel (display-only map).
        app_name: Title / side-panel header.
        show_config_tool: Show a "Copy config" button that extracts the current
            map config as JSON (paste it back as ``config=`` to reuse a styling).
        release: Base URL of the slim release to load assets from.
    """
    slim_js = f"{release}/keplergl.slim.min.js"
    slim_css = f"{release}/keplergl.min.css"

    try:
        import geopandas as gpd
    except Exception:  # geopandas optional; only needed for GeoDataFrames
        gpd = None

    rows = []
    for name, data in datasets.items():
        info = json.dumps({"id": name, "label": name})
        if gpd is not None and isinstance(data, gpd.GeoDataFrame):
            gdf = data.to_crs(4326) if data.crs else data
            geojson = json.loads(gdf.to_json(default=str))
            rows.append(
                f"        datasets.push({{info:{info}, "
                f"data: keplerGl.processGeojson({json.dumps(geojson)})}});"
            )
        elif isinstance(data, dict):  # raw GeoJSON
            rows.append(
                f"        datasets.push({{info:{info}, "
                f"data: keplerGl.processGeojson({json.dumps(data)})}});"
            )
        elif isinstance(data, str):  # raw CSV string
            rows.append(
                f"        datasets.push({{info:{info}, "
                f"data: keplerGl.processCsvData({json.dumps(data)})}});"
            )
        else:  # assume pandas DataFrame (or anything with .to_csv)
            csv = data.to_csv(index=False)
            rows.append(
                f"        datasets.push({{info:{info}, "
                f"data: keplerGl.processCsvData({json.dumps(csv)})}});"
            )

    doc = (
        _TEMPLATE
        .replace("__SLIM_JS__", slim_js)
        .replace("__SLIM_CSS__", slim_css)
        .replace("__MAPBOX_TOKEN__", json.dumps(mapbox_token))
        .replace("__READ_ONLY__", "true" if read_only else "false")
        .replace("__CENTER_MAP__", "true" if center_map else "false")
        .replace("__APP_NAME__", _html.escape(app_name))
        .replace("__DATASETS__", "\n".join(rows))
        .replace("__CONFIG__", json.dumps(config or {}))
        .replace("__CONFIG_TOOL_HTML__", _CONFIG_TOOL_HTML if show_config_tool else "")
    )

    # Guarantee only the slim build is referenced — never the generic CDN bundle.
    assert slim_js in doc, "slim JS URL was not injected"
    assert "unpkg.com/kepler.gl" not in doc, "a generic kepler.gl CDN bundle is still referenced!"
    return doc


def render(datasets: Dict[str, Any], height: int = 700, **kwargs):
    """Render the map for a Hex/Jupyter cell via ``IPython.display.IFrame``.

    The map document is base64-encoded into a ``data:`` URL and loaded as the
    iframe's ``src``. This matters in Hex: a document loaded by ``src`` is its
    own browsing context and does NOT inherit Hex's restrictive page CSP, so
    kepler.gl's scripts actually execute. (A ``srcdoc`` iframe inherits the
    parent CSP and renders blank.)

    Extra keyword args are forwarded to :func:`kepler_html` (mapbox_token,
    config, read_only, center_map, app_name, release).
    """
    import base64

    from IPython.display import IFrame  # imported lazily so the module imports outside notebooks

    doc = kepler_html(datasets, **kwargs)
    b64 = base64.b64encode(doc.encode("utf-8")).decode("ascii")
    return IFrame(src=f"data:text/html;base64,{b64}", width="100%", height=int(height))
