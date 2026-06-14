// Analysis build: same as umd-esbuild.config.mjs but emits a metafile
// and supports excluding feature packages via KEPLER_EXCLUDE env (comma-separated).
import esbuild from 'esbuild';
import {replace} from 'esbuild-plugin-replace';
import {umdWrapper} from 'esbuild-plugin-umd-wrapper';
import fs from 'node:fs';
import process from 'node:process';
const KeplerPackage = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url)));

const exclude = (process.env.KEPLER_EXCLUDE || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);
const outfile = process.env.KEPLER_OUT || './umd/keplergl.analyze.js';

const stubPlugin = {
  name: 'stub-excluded',
  setup(build) {
    if (!exclude.length) return;
    const filter = new RegExp(
      '^(' + exclude.map(e => e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')(/|$)'
    );
    build.onResolve({filter}, args => ({path: args.path, namespace: 'stub'}));
    build.onLoad({filter: /.*/, namespace: 'stub'}, () => ({
      contents: 'export default {}; export const __stubbed = true;',
      loader: 'js'
    }));
  }
};

const result = await esbuild.build({
  entryPoints: ['./src/index.js'],
  bundle: true,
  platform: 'browser',
  outfile,
  format: 'umd',
  logLevel: 'error',
  minify: true,
  sourcemap: false,
  treeShaking: true,
  metafile: true,
  external: ['react', 'react-dom', 'redux', 'react-redux', 'styled-components'],
  plugins: [
    stubPlugin,
    replace({
      __PACKAGE_VERSION__: KeplerPackage.version,
      include: /constants\/src\/default-settings\.ts/
    }),
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
}).catch(e => {
  console.error(e);
  process.exit(1);
});

const metaPath = outfile.replace(/\.js$/, '.meta.json');
fs.writeFileSync(metaPath, JSON.stringify(result.metafile));
const bytes = fs.statSync(outfile).size;
console.log(`OUT ${outfile} ${(bytes / 1048576).toFixed(2)} MB`);
console.log(`META ${metaPath}`);
