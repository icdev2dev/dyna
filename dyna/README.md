# Big picture
The app is a desktop-like Canvas that hosts multiple windows/panels (Form, Chat, Metadata). 

Each window is a movable/resizable panel inside WindowFrame.svelte.

Canvas uses a renderer registry (WINDOW_RENDERERS) to map a window kind to a small adapter component (RenderForm, RenderChat, RenderMetadata).


# Plugin 
This feature adds a new window kind: plugin. It lets you load a Svelte component at runtime and show it as just another window on the canvas.

## Short version 

Plugins give you runtime flexibility, isolation, and SAFE guardrails, but you lose some ergonomics and tight integration you get with static, first‑class Svelte components.



## What “dynamic plugin” adds

New window kind: plugin. It behaves like every other window (drag, resize, focus, close), but its UI comes from a module you compile and serve separately.

Self-contained plugin bundle: the plugin’s index.js includes the Svelte runtime and exports:

default: the Svelte 5 function component

mountPlugin(target, props): a helper that mounts the component using the plugin’s own runtime

Safe mounting: RenderPlugin dynamically imports the plugin module, then calls mountPlugin inside the window body. No host/runtime mixing, no app rebuild.

Short version: Plugins give you runtime flexibility, isolation, and SAFE guardrails, but you lose some ergonomics and tight integration you get with static, first‑class Svelte components.

## Key limitations versus static components

### Developer experience

No HMR from the host: dynamic imports don’t get host dev-server hot reload. You rebuild the plugin and reload or bump version/query.
Mitigation: add a ?ts= cache-buster in dev; run a tiny “plugin-only” dev server; script a one-liner rebuild.

Weaker typing across the boundary: the host can’t type-check a plugin’s props at compile time.
Mitigation: define a small, versioned “plugin contract” and validate props at runtime.

### Runtime integration

No Svelte context/stores sharing: plugin code runs with its own runtime; it can’t “see” host context or stores.
Mitigation: expose a narrow capability API/typed bus and pass any needed values via plain props.

Prop updates aren’t automatic: with the mountPlugin approach, you either remount or the plugin must implement its own update handling.
Mitigation: standardize an optional exported update(el, props) API, or remount on key changes for MVP.
Performance and payload

Extra runtime per plugin (by design): each plugin bundles Svelte runtime (tens of KB). Multiple plugins = duplicated bytes.
Mitigation: acceptable for MVP. Later, consider a “shared runtime” mode (pin exact Svelte version and externalize 'svelte')—but that reintroduces runtime coupling and the errors you hit.

First-open latency: dynamic import adds network + parse time.
Mitigation: prefetch popular plugins; keep bundles small.
Styling and theming

CSS isolation vs. host theming: plugin styles are scoped, but they won’t automatically adopt host tokens or dark mode unless you design for it.
Mitigation: pass CSS variables (e.g., via WindowFrame) and document the theming contract.


### Accessibility and UX cohesion

A11y and shortcuts: plugins can drift from host conventions (focus traps, keyboard, labels).
Mitigation: publish an a11y checklist in the plugin contract and lint/check before allowing a plugin.

### Security and governance

You must govern what loads: unsigned/unsanctioned code is a risk if you loosen the gate.
Mitigation: signed manifests, allowlist, feature flags, kill switch, immutable audit logs (who loaded what, when).
Testing and observability

Harder to E2E as a single app: plugin code ships separately; your host tests can’t “import” it at build time.
Mitigation: contract tests for the plugin API, plus runtime smoke checks (load time, mount success, errors). Add logs/metrics around import, mount, unmount.
SSR/Prerendering

No SSR: dynamic plugin windows are client-only; you can’t prerender their content as part of the host.
Mitigation: acceptable for admin tooling; if SSR is needed, render a fallback/skeleton.
Caching/deploy

ESM module cache: the browser caches modules by URL. Updating in place without a new version can be confusing.
Mitigation: bump version for new builds; only use ?ts= cache-buster in dev.
Inter-window communication

No direct access to controller or other windows: by design (least privilege).
Mitigation: provide a vetted bus/capability object; validate messages/sizes; allowlist channels.

## Preferences

#### When to prefer static components

Tight coupling to host state, context, or stores.
You need SSR/prerender.
You want first-class type safety end-to-end.
You can ship everything together and don’t need runtime extensibility.

#### When plugins shine

You want to add/remove capabilities without rebuilding the host.
You need tenant- or user-specific extensions gated by policy.
You want isolated failure domains (a bad plugin shouldn’t crash the host).
You need an audit trail, versioned rollout, and easy rollback.


## Practical mitigations to adopt now

Keep a narrow, documented plugin API: mountPlugin(target, props) and optional unmount/update.
Runtime validation of spawn configs and props.
Theming via CSS vars from WindowFrame.
Basic observability: log plugin load time, size, mount errors.
Governance: allowlist + kill switch per plugin id/version.
This trade-off preserves SAFE guardrails and runtime flexibility, at the cost of some developer ergonomics and deeper integration you’d get with static components.



## How it fits in the existing architecture

### Canvas.svelte
Keeps the list of windows, z-order, geometry, dirty-close logic.
Picks a renderer from WINDOW_RENDERERS[w.kind] and renders it.

#### WINDOW_RENDERERS
{ form, chat, metadata, plugin }
Adding plugin is just one extra entry in this closed mapping (no arbitrary component names).

### RenderPlugin.svelte
#### Window adapter for kind: 'plugin'.
Imports the plugin module from Flask at /plugins/<id>/<version>/index.js, reads mountPlugin, and mounts into a div inside WindowFrame.
Converts incoming window props to a plain object and remounts on id/version/props change.
Flask
Serves the built plugin bundles from public/plugins/<id>/<version>/index.js (and manifest.json).
Same-origin recommended; CORS only for dev if app and Flask are on different ports.

#### What you can do with it

Open plugin windows alongside forms, chats, and metadata editors.
Open multiple instances of the same plugin window (different props).
Close/minimize/restore like any other window. Geometry persists when you bind position/size.


#### Why Svelte 5 needs mountPlugin

Svelte 5 compiles components to function components. They aren’t constructed with new.
The plugin bundle provides mountPlugin(target, props) so the plugin mounts with its own runtime. This avoids runtime-version mismatches and the “reading 'call'” errors you saw when mixing host and plugin runtimes.

## MVP build and use (for README)

### Author your plugin (Runes)
plugins/Hello.svelte
Example:
let { who = 'world' } = $props(); let count = $state(0); const inc = () => (count += 1);
Compile and bundle (Node builder)
node build-plugin.mjs ./plugins/Hello.svelte --id=hello.plugin --version=1.0.0
Outputs:
public/plugins/hello.plugin/1.0.0/index.js (ESM bundle with Svelte runtime)
public/plugins/hello.plugin/1.0.0/manifest.json


### Serve from Flask
GET /plugins/hello.plugin/1.0.0/index.js -> 200 text/javascript
Spawn in the app
controller.spawn({ kind: 'plugin', title: 'Plugin: Hello', persist: 'keep', plugin: { id: 'hello.plugin', version: '1.0.0' }, props: { who: 'Canvas' }, size: { w: 420, h: 260 }, position: { x: 80, y: 80 } })
RenderPlugin loads /plugins/hello.plugin/1.0.0/index.js, calls mountPlugin(el, { who: 'Canvas' }), and the plugin renders in a window.


### SAFE guardrails that remain

Closed renderer registry: only known kinds can render (form/chat/metadata/plugin).
Sanitized spawn configs: kind/id/version/geometry/props are validated before use.
Least-privilege: plugins receive only the plain props you pass; no controller/network access unless you explicitly expose it later.




# Design: RenderPlugin + self-contained plugin bundle

Svelte 5 function components: Svelte 5 compiles components to functions like (anchor, props). They are not class constructors. Trying new Comp({ target, props }) or mounting them with the host’s runtime can crash.
Self-contained plugin runtime: The plugin bundle (index.js) includes the Svelte runtime and exports a mount function (mountPlugin). This avoids any runtime mismatch with the host app.
Opaque mount: RenderPlugin treats the plugin as an opaque widget:
dynamically import the plugin module,
call module.mountPlugin(el, props),
keep the destroy function and clean up on unmount.
Runes-friendly binding: mountEl is a $state so the mount effect runs when the element binds. Props passed to the plugin are plain objects (not Svelte proxies).
Remount strategy: Remount on id/version change (new code) and on props change (simple, robust MVP).

## RenderPlugin.svelte (essentials)

Loads plugin module -> picks mountPlugin
Mounts into a div (bind:this={mountEl}), returns unmount cleanup
Remounts on id/version/props change
Passes only plain props to avoid proxy leakage
Index.js exported by the plugin

default: the function component (for optional direct use)
mountPlugin(target, props): uses the plugin’s own runtime (import { mount } from 'svelte') to mount the function component and returns a destroy function
How to build a plugin with Node (no Vite needed)

### Prereqs
Dev deps (in the package that owns the builder): pnpm add -D svelte esbuild
Files:
plugins/Hello.svelte (your plugin source)
build-plugin.mjs (the builder script)

#### Example plugin source (Runes)
plugins/Hello.svelte

<script> let { who = 'world' } = $props(); let count = $state(0); const inc = () => (count += 1); </script> <div style="padding:8px"> <h2>Hello, {who}!</h2> <p>Count: {count}</p> <button onclick={inc}>Increment</button> </div>
3. Builder script (compile + wrap + bundle)


#### build-plugin.mjs
// @ts-nocheck
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { compile } from 'svelte/compiler';
import { build as esbuild } from 'esbuild';

function sha256b64(buf) { return crypto.createHash('sha256').update(buf).digest('base64'); }
function parseFlags(argv) {
const flags = {};
for (const a of argv) if (a.startsWith('--')) {
const [k, v = ''] = a.slice(2).split('='); flags[k] = v;
}
return flags;
}

const [, , srcPath, ...rest] = process.argv;
if (!srcPath) { console.error('Usage: node build-plugin.mjs <src.svelte> --id=<pluginId> --version=<semver>'); process.exit(1); }
const flags = parseFlags(rest);
const pluginId = flags.id || 'hello.plugin';
const pluginVersion = flags.version || '1.0.0';

if (!/^[a-z0-9.-]{1,64}$/i.test(pluginId)) { console.error('Invalid --id'); process.exit(1); }
if (!/^[0-9]+(.[0-9]+)*(-[A-Za-z0-9.-]+)?$/.test(pluginVersion)) { console.error('Invalid --version'); process.exit(1); }

// 1) Compile Svelte -> function component JS
const source = await fs.readFile(srcPath, 'utf8');
const { js } = compile(source, { generate: 'dom', name: 'PluginRoot', dev: false });

// 2) Prepare output dir
const outDir = path.resolve('public/plugins', pluginId, pluginVersion);
await fs.mkdir(outDir, { recursive: true });

// 3) Write compiled component
const compiledPath = path.join(outDir, 'compiled.js');
await fs.writeFile(compiledPath, js.code, 'utf8');

// 4) Entry that re-exports default and a mount helper using plugin’s own runtime
const entryPath = path.join(outDir, 'entry.js');
await fs.writeFile(
entryPath,
import { mount } from 'svelte'; import Comp from './compiled.js'; export default Comp; export function mountPlugin(target, props = {}) {   return mount(Comp, { target, props }); } ,
'utf8'
);

// 5) Bundle entry (includes runtime) -> index.js
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

// 6) Manifest for bookkeeping
const jsBuf = await fs.readFile(outfile);
const manifest = {
id: pluginId,
version: pluginVersion,
moduleUrl: /plugins/${pluginId}/${pluginVersion}/index.js,
sha256: sha256b64(jsBuf),
allowed: true
};
await fs.writeFile(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');


4. Build command

As a package.json script: "scripts": { "plugin:build": "node ./build-plugin.mjs ./plugins/Hello.svelte --id=hello.plugin --version=1.0.0" }
Run: pnpm plugin:build
Outputs: public/plugins/hello.plugin/1.0.0/index.js public/plugins/hello.plugin/1.0.0/manifest.json


### Serve with Flask 

#### Minimal route (you already have this):
@app.route('/plugins/path:subpath')
def serve_plugin_asset(subpath):
full = safe_join(PLUGINS_ROOT, subpath)
if not full or not os.path.isfile(full): return abort(404)
if full.endswith('.js'):  return send_from_directory(PLUGINS_ROOT, subpath, mimetype='text/javascript', cache_timeout=0)
if full.endswith('.json'): return send_from_directory(PLUGINS_ROOT, subpath, mimetype='application/json', cache_timeout=0)
return send_from_directory(PLUGINS_ROOT, subpath, cache_timeout=0)

Verify in browser:
http://127.0.0.1:5000/plugins/hello.plugin/1.0.0/index.js

### Use in the app (RenderPlugin)

#### RenderPlugin dynamically imports the module and calls mountPlugin(el, props).
<script> import WindowFrame from './WindowFrame.svelte'; let { w, onFocus: onFocusCb, onRequestClose: onRequestCloseCb } = $props(); let loading = $state(false), error = $state(null); let mountEl = $state(null); let mountPluginFn = $state(null); let unmount = null; async function load() { loading = true; error = null; mountPluginFn = null; try { const base = w?.plugin?.base || 'http://127.0.0.1:5000'; const url = `${base}/plugins/${w.plugin.id}/${w.plugin.version}/index.js?ts=${Date.now()}`; const mod = await import(url); mountPluginFn = mod?.mountPlugin ?? null; } catch (e) { error = String(e); } finally { loading = false; } } $effect(() => { void w?.plugin?.id; void w?.plugin?.version; load(); }); const propsKey = $derived(JSON.stringify(w?.props ?? {})); function makePlainProps() { const p = w?.props; return p && typeof p === 'object' ? { ...p } : {}; } $effect(() => { const mp = mountPluginFn, el = mountEl, _k = propsKey; if (!mp || !el) return; try { unmount?.(); } catch {} unmount = null; try { unmount = mp(el, makePlainProps()); } catch (e) { error = `Plugin mount failed: ${e}`; } return () => { try { unmount?.(); } catch {}; unmount = null; }; }); function requestClose() { onRequestCloseCb?.({ id: w.id, isDirty: false, value: null, persist: w.persist }); } </script>
<WindowFrame ...>
{#snippet children()}
{#if error}<div class="err">{error}</div>
{:else if loading}<div>Loading…</div>
{:else}<div class="plugin-mount" bind:this={mountEl}></div>
{/if}
{/snippet}
</WindowFrame>

#### Spawn a plugin window
controller.spawn({
kind: 'plugin',
title: 'Plugin: Hello',
persist: 'keep',
plugin: { id: 'hello.plugin', version: '1.0.0', base: 'http://127.0.0.1:5000' }, // base optional if same-origin
props: { who: 'Canvas' },
size: { w: 420, h: 260 },
position: { x: 80, y: 80 }
});

#### Troubleshooting

404 import: check Flask route path and that files exist in public/plugins/<id>/<version>/.
Vite dev error about public assets: use absolute import URL to Flask (as above). In production, same origin avoids this.
“reading 'who'” or “reading 'call'”: use mountPlugin from the plugin bundle; don’t use new Comp; don’t use the host’s mount for plugin function components.
Stale module: ESM modules are cached per URL. In dev, append ?ts=Date.now() when importing; in prod, bump version.
Why this is SAFE

No arbitrary code execution from schemas; only allowlisted plugin kinds render via a registry.
Least privilege: the plugin gets only the props you pass. No controller or network capabilities unless explicitly provided.
Versioned, immutable artifacts: clear rollback path (change version).
Works with strict CSP: scripts loaded from your Flask origin; no unsafe-eval or blob URLs required.