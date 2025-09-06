<script>
    import WindowFrame from './WindowFrame.svelte';

    // Props (WindowFrame contract)
    let {
        id,
        title = 'Task Graph',
        position = $bindable({ x: 80, y: 80 }),
        size = $bindable({ w: 960, h: 600 }),
        z = $bindable(1),
        persist = 'keep',
        onFocus: onFocusCb,
        onRequestClose: onRequestCloseCb,
        initialPrompt = '',
        autoGenerate = false
    } = $props();

    // UI state
    let prompt = $state('');
    let loading = $state(false);
    let error = $state(null);
    let graph = $state(null); // { tasks, roots?, edges? }

    // Layout state (computed from graph)
    let layout = $state({ nodes: [], edges: [], size: { w: 800, h: 600 } });


    $effect(() => {
    if (initialPrompt && !prompt) {
    prompt = initialPrompt;
    }
    });

    $effect(() => {
    if (autoGenerate && prompt && !loading && !graph) {
    generate(); // call your existing generate()
    }
    });


    // Fetch TaskGraph from backend (expects your backend to call BAML GenerateTaskGraph)
    async function generate() {
        const txt = prompt.trim();
        if (!txt) return;
        error = null;
        loading = true;
        try {
        const res = await fetch('http://127.0.0.1:5000/api/generate-task-graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ in_arg: txt })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        graph = sanitizeGraph(data);
        layout = layoutGraph(graph);
        } catch (e) {
        error = e?.message || String(e);
        } finally {
        loading = false;
        }
    }

    // Optional: allow importing raw JSON TaskGraph for quick testing
    function importJSON() {
        const txt = window.prompt('Paste TaskGraph JSON:', '');
        if (!txt) return;
        try {
        const data = JSON.parse(txt);
        graph = sanitizeGraph(data);
        layout = layoutGraph(graph);
        } catch (e) {
        error = 'Invalid JSON: ' + (e?.message || String(e));
        }
    }
    function copyJSON() {
        try {
        navigator.clipboard.writeText(JSON.stringify(graph ?? {}, null, 2));
        alert('Copied TaskGraph JSON to clipboard.');
        } catch {}
    }

    function requestClose() {
        onRequestCloseCb?.({ id, isDirty: false, value: null, persist });
    }

    // ---- Graph utilities ----

    function sanitizeGraph(g) {
        const tasks = Array.isArray(g?.tasks) ? g.tasks : [];
        // Build a map of all tasks; expand nested subtasks into flat map
        const map = new Map();
        const flat = [];

        function addTask(t, parentId = null) {
        if (!t || !t.id) return;
        // Clone minimal fields we use
        const node = {
            id: String(t.id),
            title: t.title ?? t.id,
            executionMode: t.executionMode ?? 'Sequential',
            completion: t.completion ?? null,
            dependsOn: Array.isArray(t.dependsOn) ? t.dependsOn.map(String) : [],
            _parent: parentId
        };
        if (!map.has(node.id)) {
            map.set(node.id, node);
            flat.push(node);
        }
        const subs = Array.isArray(t.subtasks) ? t.subtasks : [];
        for (const c of subs) addTask(c, node.id);
        }

        for (const t of tasks) addTask(t, null);

        // Collect implied edges:
        // - parent -> child (hierarchy)
        // - dependsOn -> id (cross-task deps)
        // - DataEdge from fromTaskId -> toTaskId
        const edges = [];
        for (const n of flat) {
        if (n._parent) edges.push({ from: n._parent, to: n.id, kind: 'hier' });
        for (const d of n.dependsOn) edges.push({ from: d, to: n.id, kind: 'dep' });
        }
        const dataEdges = Array.isArray(g?.edges) ? g.edges : [];
        for (const e of dataEdges) {
        if (e?.fromTaskId && e?.toTaskId) {
            edges.push({ from: String(e.fromTaskId), to: String(e.toTaskId), kind: 'data' });
        }
        }

        // Keep declared roots if provided; else derive as those with no inbound edges
        const ids = new Set(flat.map(n => n.id));
        const inbound = new Map([...ids].map(i => [i, 0]));
        for (const e of edges) {
        if (inbound.has(e.to)) inbound.set(e.to, (inbound.get(e.to) ?? 0) + 1);
        }
        const roots = Array.isArray(g?.roots) && g.roots.length
        ? g.roots.map(String).filter(id => ids.has(id))
        : [...ids].filter(i => (inbound.get(i) ?? 0) === 0);

        return { tasks: flat, edges, roots };
    }

    function layoutGraph(g) {
        const nodes = g.tasks;
        const edges = g.edges;

        // Build adjacency and in-degrees for Kahn layering
        const idToNode = new Map(nodes.map(n => [n.id, n]));
        const out = new Map(nodes.map(n => [n.id, []]));
        const indeg = new Map(nodes.map(n => [n.id, 0]));

        for (const e of edges) {
        if (!idToNode.has(e.from) || !idToNode.has(e.to)) continue;
        out.get(e.from).push(e.to);
        indeg.set(e.to, (indeg.get(e.to) ?? 0) + 1);
        }

        // Kahn: build layers
        const layers = [];
        let frontier = nodes.filter(n => (indeg.get(n.id) ?? 0) === 0).map(n => n.id);

        const seen = new Set();
        while (frontier.length) {
        layers.push(frontier);
        const next = [];
        for (const id of frontier) {
            if (seen.has(id)) continue;
            seen.add(id);
            for (const v of out.get(id) ?? []) {
            indeg.set(v, (indeg.get(v) ?? 0) - 1);
            if ((indeg.get(v) ?? 0) === 0) next.push(v);
            }
        }
        frontier = next;
        }

        // Place nodes per layer in a tidy grid
        const NODE_W = 180;
        const NODE_H = 70;
        const GAP_X = 28;
        const GAP_Y = 90;
        const PAD = 24;

        const placed = new Map();
        let width = 0;
        let height = 0;

        layers.forEach((layer, row) => {
        const cols = layer.length || 1;
        const rowWidth = cols * NODE_W + (cols - 1) * GAP_X;
        const xStart = PAD;
        const y = PAD + row * (NODE_H + GAP_Y);
        for (let i = 0; i < cols; i++) {
            const id = layer[i];
            const x = xStart + i * (NODE_W + GAP_X);
            placed.set(id, { x, y });
        }
        width = Math.max(width, xStart + rowWidth + PAD);
        height = y + NODE_H + PAD;
        });

        // If graph had cycles, some nodes won’t get placed; place them below
        const unplaced = nodes.filter(n => !placed.has(n.id));
        if (unplaced.length) {
        const row = layers.length;
        unplaced.forEach((n, i) => {
            const x = PAD + i * (NODE_W + GAP_X);
            const y = PAD + row * (NODE_H + GAP_Y);
            placed.set(n.id, { x, y });
            width = Math.max(width, x + NODE_W + PAD);
            height = Math.max(height, y + NODE_H + PAD);
        });
        }

        // Build drawable nodes
        const vizNodes = nodes.map(n => {
        const p = placed.get(n.id) ?? { x: PAD, y: PAD };
        return {
            id: n.id,
            title: n.title ?? n.id,
            mode: n.executionMode ?? 'Sequential',
            completion: n.completion?.policy ?? null,
            x: p.x, y: p.y, w: NODE_W, h: NODE_H
        };
        });

        // Build drawable edges using cubic paths
        const vizEdges = edges
        .filter(e => placed.has(e.from) && placed.has(e.to))
        .map(e => {
            const a = placed.get(e.from);
            const b = placed.get(e.to);
            const x1 = a.x + NODE_W / 2;
            const y1 = a.y + NODE_H;
            const x2 = b.x + NODE_W / 2;
            const y2 = b.y;
            const midY = (y1 + y2) / 2;
            const d = `M ${x1},${y1} C ${x1},${midY} ${x2},${midY} ${x2},${y2}`;
            return { from: e.from, to: e.to, kind: e.kind, d };
        });

        return { nodes: vizNodes, edges: vizEdges, size: { w: Math.max(width, 800), h: Math.max(height, 480) } };
    }

    // Style helpers
    function edgeClass(k) {
        if (k === 'data') return 'edge data';
        if (k === 'dep') return 'edge dep';
        return 'edge hier';
    }
</script>

<WindowFrame
  id={id}
  title={title}
  bind:position
  bind:size
  bind:z
  onFocus={onFocusCb}
  onRequestClose={requestClose}
>
  {#snippet headerActions()}
    <div style="display:flex; gap:6px;">
      <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={importJSON}>Import JSON</button>
      <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={copyJSON}>Copy JSON</button>
      <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
    </div>
  {/snippet}

  {#snippet children()}
    <div class="tg-root">
      <div class="left">
        <label class="lbl">Describe the task(s)</label>
        <textarea rows="6" placeholder="Example: Build the service, then run unit, integration and security tests in parallel, then deploy."
                  bind:value={prompt}></textarea>
        <div class="row">
          <button class="primary" onclick={generate} disabled={loading || !prompt.trim()}>{loading ? 'Generating…' : 'Generate TaskGraph'}</button>
          {#if error}<span class="err">{error}</span>{/if}
        </div>
        {#if graph}
          <div class="meta">
            <div><strong>Nodes:</strong> {layout.nodes.length}</div>
            <div><strong>Edges:</strong> {layout.edges.length}</div>
          </div>
        {/if}
      </div>

      <div class="right">
        {#if !graph}
          <div class="empty">Enter a description and click Generate to visualize the TaskGraph.</div>
        {:else}
          <div class="stage-wrap">
            <svg class="stage" width="100%" height="100%" viewBox={`0 0 ${layout.size.w} ${layout.size.h}`} xmlns="http://www.w3.org/2000/svg">
              <defs>
                <marker id="arrow" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                  <path d="M0,0 L8,4 L0,8 z" fill="#64748b"></path>
                </marker>
              </defs>

              <!-- Edges -->
              {#each layout.edges as e (e.from + '->' + e.to + ':' + e.kind)}
                <path d={e.d} class={edgeClass(e.kind)} marker-end="url(#arrow)"></path>
              {/each}

              <!-- Nodes -->
              {#each layout.nodes as n (n.id)}
                <g class="node" transform={`translate(${n.x},${n.y})`}>
                  <rect rx="10" ry="10" width={n.w} height={n.h} class="card"></rect>
                  <text class="title" x={n.w/2} y="28" text-anchor="middle">{n.title}</text>
                  <text class="sub" x={n.w/2} y="50" text-anchor="middle">
                    {n.mode}{n.completion ? ` · ${n.completion}` : ''}
                  </text>
                </g>
              {/each}
            </svg>
          </div>
        {/if}
      </div>
    </div>
  {/snippet}
</WindowFrame>

<style>
  .tg-root {
    display: grid;
    grid-template-columns: 340px 1fr;
    gap: 12px;
    height: 100%;
  }
  .left {
    display: grid;
    grid-template-rows: auto auto auto 1fr;
    gap: 10px;
  }
  .lbl { font-size: 12px; color: #6b7280; font-weight: 700; }
  textarea {
    width: 100%;
    resize: vertical;
    padding: 10px 12px;
    border: 1px solid #d1d5db;
    border-radius: 10px;
    outline: none;
  }
  textarea:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.16); }
  .row { display: flex; gap: 8px; align-items: center; }
  .primary {
    padding: 8px 12px;
    border-radius: 10px;
    border: 1px solid #1d4ed8;
    background: #2563eb; color: #fff; font-weight: 700;
    cursor: pointer;
  }
  .err { color: #b91c1c; }
  .meta { display: flex; gap: 12px; color: #475569; font-size: 12px; }

  .right { position: relative; overflow: hidden; display: grid; }
  .empty { align-self: center; justify-self: center; color: #64748b; }
  .stage-wrap {
    position: relative;
    width: 100%; height: 100%;
    border: 1px solid #e5e7eb; border-radius: 12px; background: #fff;
    overflow: auto;
  }
  .stage { display: block; }

  /* Edges */
  .edge { fill: none; stroke: #94a3b8; stroke-width: 1.6; opacity: 0.9; }
  .edge.dep { stroke: #2563eb; }
  .edge.data { stroke: #059669; }

  /* Nodes */
  .node .card {
    fill: #ffffff;
    stroke: #e5e7eb;
    stroke-width: 1.2;
    filter: drop-shadow(0 1px 6px rgba(0,0,0,0.08));
  }
  .node .title {
    font-weight: 700;
    fill: #0f172a;
    font-size: 13px;
  }
  .node .sub {
    fill: #64748b;
    font-size: 11px;
  }
</style>
