# kepler-slim for Jupyter

[![PyPI version](https://img.shields.io/pypi/v/kepler-slim.svg)](https://pypi.org/project/kepler-slim/)
[![PyPI prerelease](https://img.shields.io/pypi/v/kepler-slim.svg?include_prereleases&label=prerelease)](https://pypi.org/project/kepler-slim/#history)

`kepler-slim` is the Jupyter widget for [kepler-slim](https://github.com/cocorobotics/kepler-slim),
an open-source, size-reduced fork of [kepler.gl](http://kepler.gl). The widget API matches
upstream `keplergl`; the difference is that **`save_to_html` exports a map that loads the slim
bundle** from the kepler-slim GitHub release (its rolling `LATEST` tag) rather than the full
kepler.gl bundle from a CDN.

The slim build uses **Mapbox** basemaps and requires a Mapbox access token (MapLibre and the AI
Assistant are removed). See the [project README](https://github.com/cocorobotics/kepler-slim#readme)
and [SLIMMING.md](https://github.com/cocorobotics/kepler-slim/blob/master/SLIMMING.md).

## Installation

```shell
pip install kepler-slim
```

The import name is still `keplergl`:

### Prerequisites
- Python >= 3.9
- JupyterLab >= 4.0 or Notebook >= 7.0

## Quick Start

```python
from keplergl import KeplerGl

# Create a map (pass a Mapbox token for the slim build's basemaps)
m = KeplerGl(height=400, mapbox_token="pk.your_token")

# Add data
m.add_data(data=df, name='my_data')

# Display the widget
m

# Export a standalone HTML map that loads the slim bundle from the LATEST release
m.save_to_html(file_name='kepler_slim_map.html')
```

## License

MIT — see the repository [LICENSE](https://github.com/cocorobotics/kepler-slim/blob/master/LICENSE).
kepler-slim is a fork of kepler.gl; the original copyright is retained.
