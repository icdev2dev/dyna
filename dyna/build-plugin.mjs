// build-plugin.mjs
// @ts-nocheck
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { compile } from 'svelte/compiler';
import { build as esbuild } from 'esbuild';

function sha256b64(buf) {
return crypto.createHash('sha256').update(buf).digest('base64');
}

function parseFlags(argv) {
const flags = {};
for (const a of argv) {
if (a.startsWith('--')) {
const [k, v = ''] = a.slice(2).split('=');
flags[k] = v;
}
}
return flags;
}

const [, , srcPath, ...rest] = process.argv;
if (!srcPath) {
console.error('Usage: node build-plugin.mjs <src.svelte> --id=<pluginId> --version=<semver>');
process.exit(1);
}
const flags = parseFlags(rest);
const pluginId = flags.id || 'hello.plugin';
const pluginVersion = flags.version || '1.0.0';

// basic hygiene
if (!/^[a-z0-9.-]{1,64}$/i.test(pluginId)) {
console.error('Invalid --id. Use letters/numbers . _ -');
process.exit(1);
}
if (!/^[0-9]+(.[0-9]+)*(-[A-Za-z0-9.-]+)?$/.test(pluginVersion)) {
console.error('Invalid --version. Use semver-like string');
process.exit(1);
}

// 1) Compile Svelte to JS (function component in Svelte 5)
const source = await fs.readFile(srcPath, 'utf8');
const { js } = compile(source, { generate: 'dom', name: 'PluginRoot', dev: false });

// 2) Prepare output dir
const outDir = path.resolve('public/plugins', pluginId, pluginVersion);
await fs.mkdir(outDir, { recursive: true });

// 3) Write compiled component to compiled.js
const compiledPath = path.join(outDir, 'compiled.js');
await fs.writeFile(compiledPath, js.code, 'utf8');

// 4) Create entry.js that re-exports default and a mountPlugin helper
//    mountPlugin uses the plugin’s own bundled Svelte runtime
const entryPath = path.join(outDir, 'entry.js');
await fs.writeFile(
    entryPath,
  `import { mount } from 'svelte';   
  import Comp from './compiled.js';   
  export default Comp;   // Use the plugin's bundled runtime to mount its function component   
  export function mountPlugin(target, props = {}) {     return mount(Comp, { target, props });   }` ,
'utf8'
);

// 5) Bundle entry.js (not compiled.js) so runtime is included in index.js
const outfile = path.join(outDir, 'index.js');
await esbuild({
entryPoints: [entryPath],
bundle: true,
format: 'esm',
outfile,
target: ['es2022'],
platform: 'browser',
legalComments: 'none',
minify: false
});

// 6) Create manifest with checksum
const jsBuf = await fs.readFile(outfile);
const moduleUrl = '/plugins/' + pluginId + '/' + pluginVersion + '/index.js';
const manifest = {
id: pluginId,
version: pluginVersion,
moduleUrl,
sha256: sha256b64(jsBuf),
allowed: true
};
await fs.writeFile(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');
