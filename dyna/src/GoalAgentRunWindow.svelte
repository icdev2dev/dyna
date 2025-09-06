<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Launch Run — GoalAgent', 
        position = $bindable({ x: 60, y: 60 }), 
        size = $bindable({ w: 1100, h: 680 }), 
        z=$bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, 
        // optional 
        seedPrompt = '' 
    } = $props(); 
    let goalText = $state(seedPrompt); 
    let loading = $state(false); 
    let error = $state(null); 
    let graph = $state(null); 
    let layout = $state({ nodes: [], edges: [], size: { w: 960, h: 560 } }); 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    async function generate() { 
        const text = goalText.trim(); 
        if (!text) return; 
        loading = true; 
        error = null; 
        try { 
            const res = await fetch('http://127.0.0.1:5000/api/generate-task-graph', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ in_arg: text }) 
            }); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); 
            graph = sanitizeGraph(data); layout = layoutGraph(graph); 
        } catch (e) { error = e?.message || String(e); } finally { loading = false; } 
    } 
    // Same sanitize/layout helpers you already use in TaskGraphWindow 
    function sanitizeGraph(g) { 
        const tasks = Array.isArray(g?.tasks) ? g.tasks : []; 
        const map = new Map(); 
        const flat = []; 
        function addTask(t, parentId=null) { 
            if (!t?.id) return; 
            const n = { 
                id:String(t.id), 
                title:t.title ?? t.id, executionMode:t.executionMode ?? 'Sequential', 
                completion:t.completion ?? null, 
                dependsOn:Array.isArray(t.dependsOn)?t.dependsOn.map(String):[], 
                _parent:parentId 
            }; 
            if (!map.has(n.id)) { map.set(n.id,n); flat.push(n); } 
            for (const c of (t.subtasks??[])) addTask(c, n.id); 
        } 
        for (const t of tasks) addTask(t,null); 
        const edges=[]; 
        for (const n of flat) { 
            if (n._parent) edges.push({from:n._parent,to:n.id,kind:'hier'}); 
            for (const d of n.dependsOn) edges.push({from:d,to:n.id,kind:'dep'}); 
        } 
        for (const e of (g?.edges??[])) { 
            if (e?.fromTaskId && e?.toTaskId) edges.push({from:String(e.fromTaskId),to:String(e.toTaskId),kind:'data'}); 
        } 
        const ids = new Set(flat.map(n=>n.id)); 
        const inbound=new Map([...ids].map(i=>[i,0])); 
        for (const e of edges) if (inbound.has(e.to)) inbound.set(e.to,(inbound.get(e.to)??0)+1); 
        const roots = Array.isArray(g?.roots) && g.roots.length ? g.roots.map(String).filter(id=>ids.has(id)) : [...ids].filter(i => (inbound.get(i)??0)===0); 
        return { tasks: flat, edges, roots }; 
    } 
    
    function layoutGraph(g) { 
        const nodes=g.tasks, edges=g.edges; 
        const idToNode=new Map(nodes.map(n=>[n.id,n])); 
        const out=new Map(nodes.map(n=>[n.id,[]])); 
        const indeg=new Map(nodes.map(n=>[n.id,0])); 
        for (const e of edges) { 
            if (!idToNode.has(e.from)||!idToNode.has(e.to)) continue; 
            out.get(e.from).push(e.to); 
            indeg.set(e.to,(indeg.get(e.to)??0)+1); 
        } 
        const layers=[]; 
        let frontier=nodes.filter(n=>(indeg.get(n.id)??0)===0).map(n=>n.id); 
        const seen=new Set(); 
        while(frontier.length){ 
            layers.push(frontier); 
            const next=[]; 
            for(const id of frontier){ 
                if(seen.has(id)) continue; 
                seen.add(id); 
                for(const v of out.get(id)??[]){ 
                    indeg.set(v,(indeg.get(v)??0)-1); 
                    if((indeg.get(v)??0)===0) next.push(v);
                } 
            } 
            frontier=next; 
        } 
        const NODE_W=180,NODE_H=70,GAP_X=28,GAP_Y=90,PAD=24; 
        const placed=new Map(); 
        let width=0,height=0; 
        layers.forEach((layer,row)=>{ 
            const cols=layer.length||1; 
            const rowWidth=cols*NODE_W+(cols-1)*GAP_X; 
            const xStart=PAD; 
            const y=PAD+row*(NODE_H+GAP_Y); 
            for (let i=0;i<cols;i++){ 
                const id=layer[i]; 
                const x=xStart+i*(NODE_W+GAP_X); placed.set(id,{x,y}); 
            } 
            width=Math.max(width,xStart+rowWidth+PAD); 
            height=y+NODE_H+PAD; 
        }); 
        const unplaced=nodes.filter(n=>!placed.has(n.id)); 
        if(unplaced.length){ 
            const row=layers.length; 
            unplaced.forEach((n,i)=>{ 
                const x=PAD+i*(NODE_W+GAP_X); 
                const y=PAD+row*(NODE_H+GAP_Y); 
                placed.set(n.id,{x,y}); 
                width=Math.max(width,x+NODE_W+PAD); 
                height=Math.max(height,y+NODE_H+PAD); 
                }); 
        } 
        const vizNodes=nodes.map(n=>{ const p=placed.get(n.id)??{x:PAD,y:PAD}; 
        return { id:n.id, title:n.title??n.id, mode:n.executionMode??'Sequential', completion:n.completion?.policy??null, x:p.x,y:p.y,w:180,h:70 }; 
        });

        const vizEdges=edges.filter(e=>placed.has(e.from)&&placed.has(e.to)).map(e=>{ const a=placed.get(e.from), b=placed.get(e.to); const x1=a.x+90, y1=a.y+70, x2=b.x+90, y2=b.y, midY=(y1+y2)/2; 
        const d=`M ${x1},${y1} C ${x1},${midY} ${x2},${midY} ${x2},${y2}`; 
        return {from:e.from,to:e.to,kind:e.kind,d}; }); 
        return { nodes: vizNodes, edges: vizEdges, size: { w: Math.max(width, 960), h: Math.max(height, 560) } }; 
    } 
    
    function edgeClass(k){ 
        if(k==='data') return 'edge data'; 
        if(k==='dep') return 'edge dep'; 
        return 'edge hier'; 
    } 
    $effect(() => { if (seedPrompt && !graph && !loading) generate(); }); 
</script>

<WindowFrame
    id={id}
    title={title}
    bind:position
    bind:size
    {z}

    onFocus={onFocusCb}
    onRequestClose={requestClose}>

{#snippet children()}
<div class="gp-root">
<aside class="left">
<div class="sec">
<label class="lbl">Describe your goal</label>
<textarea rows="6" bind:value={goalText} placeholder="We’ll turn this into a TaskGraph…"></textarea>
<div class="row">
<button class="btn primary" onclick={generate} disabled={loading || !goalText.trim()}>
{loading ? 'Generating…' : 'Generate Graph'}
</button>
{#if error}<span class="err">{error}</span>{/if}
</div>
</div>
</aside>


<main class="right">
    {#if !graph}
        <div class="empty">Enter a goal and click Generate to see a TaskGraph.</div>
    {:else}
        <div class="stage-wrap">
            <svg
                class="stage"
                width="100%"
                height="100%"
                viewBox={`0 0 ${layout.size.w} ${layout.size.h}`}
                xmlns="http://www.w3.org/2000/svg"
            >
            <defs>
                <marker
                id="arrow"
                viewBox="0 0 8 8"
                refX="6"
                refY="4"
                markerWidth="8"
                markerHeight="8"
                orient="auto-start-reverse"
                >
                <path d="M0,0 L8,4 L0,8 z" fill="#64748b"></path>
                </marker>
            </defs>

            {#each layout.edges as e (e.from + '->' + e.to + ':' + e.kind)}
                <path d={e.d} class={edgeClass(e.kind)} marker-end="url(#arrow)"></path>
            {/each}

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
</main>

</div>

{/snippet}
</WindowFrame>

<style> 
    .gp-root { display: grid; grid-template-columns: 360px 1fr; gap: 12px; height: 100%; } 
    .left { display: grid; grid-auto-rows: auto 1fr; gap: 12px; } 
    .sec { display: grid; gap: 8px; } 
    .lbl { font-size: 12px; color: #6b7280; font-weight: 700; } 
    textarea { width: 100%; resize: vertical; min-height: 120px; padding: 10px 12px; border:1px solid #d1d5db; border-radius:10px; outline: none; } 
    textarea:focus { border-color:#2563eb; box-shadow:0 0 0 3px rgba(37,99,235,.16); } 
    .row { display:flex; gap:8px; align-items:center; } 
    .btn { padding:8px 12px; border-radius:10px; border:1px solid #cbd5e1; background:#fff; cursor:pointer; } 
    .btn.primary { border-color:#1d4ed8; background:#2563eb; color:#fff; font-weight:700; } 
    .right { position:relative; overflow:hidden; display:grid; } 
    .empty { align-self:center; justify-self:center; color:#64748b; } 
    .stage-wrap { width:100%; height:100%; border:1px solid #e5e7eb; border-radius:12px; background:#fff; overflow:auto; } 
    .edge { fill:none; stroke:#94a3b8; stroke-width:1.6; opacity:.9; } 
    .edge.dep { stroke:#2563eb; } 
    .edge.data { stroke:#059669; } 
    .node .card { fill:#fff; stroke:#e5e7eb; stroke-width:1.2; filter: drop-shadow(0 1px 6px rgba(0,0,0,.08)); } 
    .node .title { font-weight:700; fill:#0f172a; font-size:13px; } 
    .node .sub { fill:#64748b; font-size:11px; } 
    .err { color:#b91c1c; } 
</style>
