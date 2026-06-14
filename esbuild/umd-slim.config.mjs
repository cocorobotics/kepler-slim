// SPDX-License-Identifier: MIT
// Copyright contributors to the kepler.gl project
//
// Slim UMD build for embedding kepler.gl in size-constrained web views (e.g. Hex, 10MB limit).
//
// Produces ./umd/keplergl.slim.min.js (~9.4MB vs ~14.2MB for the full build:umd) by removing,
// at bundle time only (no source edits), features that are not needed for an embedded map:
//   - the AI Assistant (@kepler.gl/ai-assistant + its echarts/openassistant/ai-sdk tree): ~3.8MB
//   - the MapLibre basemap renderer (maplibre-gl + @vis.gl/react-maplibre): ~0.8MB
//
// Because MapLibre is removed, this build defaults to a Mapbox basemap style ('dark') instead of
// the Carto/MapLibre default ('dark-matter'). The embedding app MUST provide a Mapbox access
// token. Carto's free MapLibre basemaps are not available in this build.
//
// See SLIMMING.md for the full size analysis and how to adjust which features are dropped.

import esbuild from 'esbuild';
import {umdWrapper} from 'esbuild-plugin-umd-wrapper';
import fs from 'node:fs';
import process from 'node:process';

const KeplerPackage = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url)));

// Literal source patches applied at bundle time (no on-disk edits). Each patch fails loudly if
// its `find` string is no longer present, so an upstream rename can never silently ship an
// unpatched (broken) bundle. We use plain string replacement rather than esbuild-plugin-replace,
// whose default `\b` word-boundary delimiters silently fail to match keys ending in `;` or `'`.
const SOURCE_PATCHES = [
  {
    file: /constants\/src\/default-settings\.ts$/,
    find: '__PACKAGE_VERSION__',
    replace: KeplerPackage.version
  },
  {
    // MapLibre is removed, so default to a Mapbox basemap style instead of Carto's 'dark-matter'.
    file: /constants\/src\/default-settings\.ts$/,
    find: "DEFAULT_BASE_MAP_STYLE = 'dark-matter'",
    replace: "DEFAULT_BASE_MAP_STYLE = 'dark'"
  },
  {
    // MapLibre's React Map component is stubbed to `undefined`, so it must never be rendered.
    // getBaseMapLibrary() falls back to MAPLIBRE for unresolved/non-Mapbox styles (incl. the first
    // render before the style loads), which would render `undefined` -> React error #130. Force it
    // to always resolve to MAPBOX so the (bundled) Mapbox adapter is always used.
    file: /map-style-utils\/mapbox-utils\.ts$/,
    find: 'return MAP_LIB_OPTIONS.MAPLIBRE;',
    replace: 'return MAP_LIB_OPTIONS.MAPBOX;'
  }
];

const sourcePatchPlugin = {
  name: 'kepler-slim-source-patches',
  setup(build) {
    build.onLoad({filter: /\.tsx?$/}, async args => {
      const applicable = SOURCE_PATCHES.filter(p => p.file.test(args.path));
      if (!applicable.length) return null; // let esbuild load it normally
      let src = await fs.promises.readFile(args.path, 'utf8');
      for (const p of applicable) {
        if (!src.includes(p.find)) {
          throw new Error(`[kepler-slim] source patch did not match in ${args.path}: ${p.find}`);
        }
        src = src.split(p.find).join(p.replace);
      }
      return {contents: src, loader: args.path.endsWith('.tsx') ? 'tsx' : 'ts'};
    });
  }
};

// Packages to remove from the slim bundle. Each is replaced with an empty CommonJS module so that
// any named imports resolve to `undefined` (esbuild won't error) and any `import()` of them yields
// an empty module. These code paths are only reached when the corresponding feature is actually
// used (AI Assistant panel / MapLibre basemap), which this build intentionally disables.
const STUBBED = [
  '@kepler.gl/ai-assistant',
  'maplibre-gl',
  '@vis.gl/react-maplibre',
  'maplibregl-mapbox-request-transformer'
];

const stubFilter = new RegExp(
  '^(' + STUBBED.map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')(/|$)'
);

const stubPlugin = {
  name: 'kepler-slim-stub',
  setup(build) {
    build.onResolve({filter: stubFilter}, args => ({
      path: args.path,
      namespace: /\.(css|scss)$/.test(args.path) ? 'slim-stub-css' : 'slim-stub'
    }));
    build.onLoad({filter: /.*/, namespace: 'slim-stub'}, () => ({
      contents: 'module.exports = new Proxy(function(){}, {get: () => undefined});',
      loader: 'js'
    }));
    build.onLoad({filter: /.*/, namespace: 'slim-stub-css'}, () => ({contents: '', loader: 'css'}));
  }
};

await esbuild
  .build({
    entryPoints: ['./src/index.js'],
    bundle: true,
    platform: 'browser',
    outfile: './umd/keplergl.slim.min.js',
    format: 'umd',
    logLevel: 'error',
    minify: true,
    sourcemap: false,
    treeShaking: true,
    external: ['react', 'react-dom', 'redux', 'react-redux', 'styled-components'],
    plugins: [
      stubPlugin,
      sourcePatchPlugin,
      umdWrapper({
        libraryName: 'KeplerGl',
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
          redux: 'Redux',
          'react-redux': 'ReactRedux',
          'styled-components': 'styled'
        }
      })
    ]
  })
  .catch(e => {
    console.error(e);
    process.exit(1);
  });

const bytes = fs.statSync('./umd/keplergl.slim.min.js').size;
console.log(`built umd/keplergl.slim.min.js  ${(bytes / 1048576).toFixed(2)} MB raw`);
