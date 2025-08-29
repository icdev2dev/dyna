<script> 
  import WindowFrame from './WindowFrame.svelte'; 



  import LiveRunWindow from './LiveRunWindow.svelte'; 
  // ...your existing code... 
 // Track opened live windows (each one is a LiveRunWindow) 
  let liveWindows = $state([]); 
  // [{ id, agent_id, session_id }] 
  
  function openLiveRun(run) { 
    closeMenu(); 
    console.log(run)
    if (!run?.agent_id || !run?.session_id) return; 
    const id = crypto.randomUUID(); 
    liveWindows = [ ...liveWindows, { id, agent_id: run.agent_id, session_id: run.session_id } ]; 
  } 
  function closeLiveRun(id) { 
    liveWindows = liveWindows.filter(w => w.id !== id); 
  } 
  // Replace the old "viewLastUpdated" to open live window instead function viewLastUpdated(run) { openLiveRun(run); }


  let { 
    id, 
    title = 'Agent Runs', 
    position = $bindable({ x: 140, y: 120 }), 
    size = $bindable({ w: 900, h: 520 }), 
    z = $bindable(1), persist = 'keep', 
    onFocus: onFocusCb, onRequestClose: onRequestCloseCb, 
    // optional initial filters 
    filters = $bindable({ agent_id: '', status: '', q: '' }) 
  } = $props(); 
  let loading = $state(false); 
  let error = $state(null); 
  let runs = $state([]); 
  let sortBy = $state('created_at'); 
  let sortDir = $state('desc'); 
  // 'asc' | 'desc' 
  let expanded = $state(null); 
  // run id to show JSON details 
  // New: row action menu state 
  let menuOpen = $state(false); 
  let menuX = $state(0), menuY = $state(0); 
  let menuRun = $state(null); 
  // New: interrupt guidance modal 
  let interruptOpen = $state(false); 
  let guidanceText = $state(''); 
  let interruptBusy = $state(false); 
  let interruptError = $state(null); 
  function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
  function fmtDate(d) { if (!d) return ''; try { const dt = typeof d === 'string' || typeof d === 'number' ? new Date(d) : d; if (Number.isNaN(dt.getTime())) return String(d); return dt.toLocaleString(); } catch { return String(d); } } 
  function calcDurationMs(start, end) { const s = start ? new Date(start).getTime() : NaN; const e = end ? new Date(end).getTime() : NaN; if (!Number.isFinite(s) || !Number.isFinite(e)) return null; return Math.max(0, e - s); } 
  function fmtDuration(ms) { if (ms == null) return ''; const sec = Math.floor(ms / 1000); const h = Math.floor(sec / 3600); const m = Math.floor((sec % 3600) / 60); const s = sec % 60; if (h) return `${h}h ${m}m ${s}s`; if (m) return `${m}m ${s}s`; return `${s}s`; } 
  function toInt(v, fallback = null) { const n = Number(v); return Number.isFinite(n) ? Math.trunc(n) : fallback; } 
  function ensureJSONString(v) { if (v == null) return null; if (typeof v === 'string') return v; try { return JSON.stringify(v); } catch { return String(v); } } 
  // Fix: define id and also capture a "last_text" preview for the menu 
  function normalizeRun(r) { const id = r.id ?? r.run_id ?? r.runId ?? r.session_id ?? ''; const agent_id = r.agent_id ?? r.agentId ?? ''; const created_at = r.created_at ?? r.last_updated ?? r.started_at ?? r.start_time ?? r.started ?? r.startTime ?? r.timestamp ?? null; const session_id = r.session_id ?? r.sessionId ?? null; const iteration = toInt(r.iteration, 0); const status = r.status ?? r.step_status ?? r.result_status ?? null; const last_text = r.text ?? r.message ?? r.output ?? null; let latency_ms = toInt(r.latency_ms, null); const finished_raw = r.finished_at ?? r.end_time ?? r.ended ?? r.endTime ?? r.completed_at ?? null; if (latency_ms == null && created_at && finished_raw) { const s = new Date(created_at).getTime(); const e = new Date(finished_raw).getTime(); if (Number.isFinite(s) && Number.isFinite(e)) latency_ms = Math.max(0, e - s); } const error = r.error ?? r.err ?? null; const run_id = id; const started_at = created_at ?? null; const finished_at = finished_raw; const duration_ms = latency_ms != null ? latency_ms : 0; return { ...r, id, agent_id, session_id, created_at, iteration, status, latency_ms, error, last_text, run_id, started_at, finished_at, duration_ms }; } 
  async function refresh() { 
    loading = true; error = null; 
    try { 
      const params = new URLSearchParams(); 
      if (filters.agent_id) params.set('agent_id', filters.agent_id); 
      if (filters.status) params.set('status', filters.status); 
      if (filters.q) params.set('q', filters.q); 
      const url = 'http://127.0.0.1:5000/api/list-sessions-for-agent' + (params.toString() ? `?${params.toString()}` : ''); 
      const res = await fetch(url); 
      if (!res.ok) throw new Error(`Server error: ${res.status}`); 
      const data = await res.json(); 
      runs = Array.isArray(data) ? data.map(normalizeRun) : []; sortNow(); 
    } catch (e) { error = e.message || String(e); } loading = false; } 
    function sortNow() { 
      const dir = sortDir === 'asc' ? 1 : -1; 
      const key = sortBy; 
      const sorted = [...runs].sort((a, b) => { 
        const va = a[key]; 
        const vb = b[key]; 
        if (va == null && vb == null) return 0; 
        if (va == null) return 1; 
        if (vb == null) return -1; 
        if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir; 
        const sa = String(va); 
        const sb = String(vb); 
        return sa.localeCompare(sb) * dir; 
      }); 
      runs = sorted; 
    } 
    function setSort(col) { 
      if (sortBy === col) { 
        sortDir = sortDir === 'asc' ? 'desc' : 'asc'; 
      } 
      else { 
        sortBy = col; 
        sortDir = 'desc'; 
      } 
      sortNow(); 
    } 
    function exportCSV() { 
      const cols = ['run_id', 'agent_id', 'status', 'started_at', 'finished_at', 'duration_ms']; 
      const header = cols.join(','); 
      const lines = runs.map(r => cols.map(c => { const v = r[c]; const s = v == null ? '' : String(v).replace(/"/g, '""'); 
      return `"${s}"`; }).join(',')); 
      const blob = new Blob([header + '\n' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' }); 
      const url = URL.createObjectURL(blob); 
      const a = document.createElement('a'); 
      a.href = url; 
      a.download = 'agent_runs.csv'; 
      document.body.appendChild(a); 
      a.click(); 
      a.remove(); 
      URL.revokeObjectURL(url); 
    } 
    function dash(v) { return v == null || v === '' ? '—' : v; } 
    function tryParseJSON(s) { 
      if (typeof s !== 'string') return null; 
      try { 
        return JSON.parse(s); 

      } catch { return null; } 
    } 
    function prettyJSONorRaw(s) { const obj = tryParseJSON(s); return obj ? JSON.stringify(obj, null, 2) : s ?? ''; } 
    function hasJSON(s) { return typeof s === 'string' && tryParseJSON(s) != null; } 
    $effect(() => { refresh(); }); 
    $effect(() => { JSON.stringify(filters); refresh(); });
    // refetch on filters change // Row actions 
    function openMenu(evt, run) { menuRun = run; menuX = evt.clientX; menuY = evt.clientY; menuOpen = true; } 
    function closeMenu() { menuOpen = false; menuRun = null; } 
    function viewDetails(run) { alert('Run details:\n' + JSON.stringify(run, null, 2)); closeMenu(); } 







    

//    function viewLastUpdated(run) { 
//      const text = run.last_text ? String(run.last_text) : '(no last text available)'; 
//      alert(`Last updated text:\n\n${text}`); 
//      closeMenu(); 
//    }
    
    

async function viewLastUpdated(run) {
const sid = run?.session_id;
try {

  const url = 'http://127.0.0.1:5000/api/get-last-step-for-session_id?session_id=' + `${encodeURIComponent(sid)}` 

//  const url = sid ? /api/get-last-step-for-session_id?session_id=${encodeURIComponent(sid)}:
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  
  const data = await res.json();
  const text = typeof data === 'string' ? data
  : data?.last_step ?? data?.text ?? String(data);
  alert('Last updated text:\n\n' + (text ?? ''));
} catch (e) {
alert('Error: ' + (e?.message ?? String(e)));
} finally {
closeMenu();
}
}


  function openInterrupt(run) { 
    guidanceText = ''; 
    interruptError = null; 
    interruptOpen = true; 
    menuRun = run; 
    menuOpen = false; 
  } 
  function cancelInterrupt() { 
    if (interruptBusy) return; 
    interruptOpen = false; 
    interruptError = null; 
    guidanceText = ''; 
    menuRun = null; 
  } 
  


async function confirmInterrupt() {
  interruptBusy = true;
  interruptError = null;
  const session_id = menuRun?.session_id;
  if (!session_id) {
    interruptError = 'No session_id';
    interruptBusy = false;
    return;
  }
  try {
    const res = await fetch('http://127.0.0.1:5000/api/interrupt-agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, guidance: guidanceText })
    });
    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    interruptOpen = false;
    menuRun = null;
    guidanceText = '';
  } catch (e) {
    interruptError = e.message || String(e);
  } finally {
    interruptBusy = false;
  }
}    


  async function confirmResume(session_id) {

    try { // Example payload (adjust to your API): // 
      await fetch('http://127.0.0.1:5000/api/resume-agent', 
      {  
        method: 'POST',  
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(session_id) 
      });

      alert(`Resumed run (session_id=${menuRun?.session_id})`); 
      menuRun = null; 
    } catch (e) { interruptError = e.message || String(e); } finally { interruptBusy = false; } 
  
    
  }


  async function confirmPause(session_id) {

    try { // Example payload (adjust to your API): // 
      await fetch('http://127.0.0.1:5000/api/pause-agent', 
      {  
        method: 'POST',  
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(session_id) 
      });

      alert(`Paused run (session_id=${menuRun?.session_id})`); 
      menuRun = null; 
    } catch (e) { interruptError = e.message || String(e); } finally { interruptBusy = false; } 
  
    
  }
  
  async function confirmStop(session_id) {
  
    try { // Example payload (adjust to your API): // 
      await fetch('http://127.0.0.1:5000/api/stop-agent', 
      {  
        method: 'POST',  
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(session_id) 
      });

      alert(`Stopped run (session_id=${menuRun?.session_id})`); 
      menuRun = null; 
      guidanceText = ''; 
    } catch (e) { interruptError = e.message || String(e); } finally { interruptBusy = false; } 
  
  }


    async function deleteRun(run) { // High-level stub only; wire to your API later 
      if (!window.confirm('Delete this run?')) return; 
      try { 
        await fetch(`http://127.0.0.1:5000/api/delete-run?session_id=${encodeURIComponent(run.session_id)}`, 
          { method: 'DELETE' 

          }); 
      alert(`Would delete run (session_id=${run.session_id})`); 
      // Reflect locally for now 
      runs = runs.filter(r => r.session_id !== run.session_id); 
      } finally { closeMenu(); 

    } 
  } 
</script>

<WindowFrame
  {id}
  {title}
  bind:position
  bind:size
  {z}
  onFocus={onFocusCb}
  onRequestClose={requestClose} >

  {#snippet children()}

    <section class="runs-root"> <div class="toolbar"> <div class="filters"> <div class="field"> <label>Agent ID</label> <input type="text" placeholder="e.g. agent-123" bind:value={filters.agent_id} /> </div> <div class="field"> <label>Status</label> <select bind:value={filters.status}> <option value="">Any</option> <option value="running">running</option> <option value="succeeded">succeeded</option> <option value="failed">failed</option> <option value="stopped">stopped</option> </select> </div> <div class="field"> <label>Search</label> <input type="text" placeholder="run id, text…" bind:value={filters.q} /> </div> </div> <div class="actions"> <button type="button" onclick={refresh} title="Refresh">⟳ Refresh</button> <button type="button" onclick={exportCSV} title="Export CSV">⇩ Export CSV</button> </div> </div>
    {#if loading}
    <div class="loading">Loading…</div>
    {:else if error}
    <div class="err">Error: {error}</div>
    {:else}
    {#if runs.length}
    <div class="table-wrap">
    <table class="runs-table">
    <thead>
    <tr>
    <th onclick={() => setSort('agent_id')} class:selected={sortBy==='agent_id'}>Agent</th>
    <th onclick={() => setSort('status')} class:selected={sortBy==='status'}>Status</th>
    <th onclick={() => setSort('session_id')} class:selected={sortBy==='session_id'}>Session Id</th>
    <th onclick={() => setSort('created_at')} class:selected={sortBy==='created_at'}>Last Updated</th>
    <th>Actions</th>
    </tr>
    </thead>
    <tbody>
    {#each runs as r}
    <tr>
    <td>{r.agent_id}</td>
    <td class={'status ' + (r.status || '').toLowerCase()}>{r.status}</td>
    <td>{r.session_id}</td>
    <td>{fmtDate(r.created_at)}</td>
    <td class="row-actions">
    <button
    type="button"
    class="action-btn"
    title="Actions"
    onclick={(e) => openMenu(e, r)}
    >⋯</button>
    </td>
    </tr>
    {/each}
    </tbody>
    </table>
    </div>
    {:else}
    <div class="empty">No runs found for current filters.</div>
    {/if}
    {/if}

    </section> 
  {/snippet} 
</WindowFrame>
{#if menuOpen}

  <div class="popover-menu" style={`left: ${menuX}px; top: ${menuY}px;`} onclick={e => e.stopPropagation()} > 
    <div class="pmenu-label"> Last updated: {fmtDate(menuRun?.created_at)} </div> 
    <button class="pmenu-btn" onclick={() => viewDetails(menuRun)}>📄 View details</button> 
    <button class="pmenu-btn" onclick={() => openLiveRun(menuRun)}>🕒 View last updated text</button> 
    {#if (menuRun?.status || '').toLowerCase() === 'running'} 
      <button class="pmenu-btn" onclick={() => confirmPause(menuRun.session_id)}>⏸️ Pause</button>
      <button class="pmenu-btn" onclick={() => confirmStop(menuRun.session_id)}>⏹️ Stop</button>
      <button class="pmenu-btn" onclick={() => openInterrupt(menuRun)}>🛑 Interrupt with guidance…</button>
    {/if} 
    {#if (menuRun?.status || '').toLowerCase() === 'paused'} 
      
      <button class="pmenu-btn" onclick={() => confirmResume(menuRun.session_id)}>▶️ Resume</button>
    {/if}
    {#if (menuRun?.status || '').toLowerCase() === 'stopped'} 
      <button class="pmenu-btn danger" onclick={() => deleteRun(menuRun)}>🗑️ Delete run</button> 
    {/if} 
  </div> 
  <div class="backdrop" onclick={closeMenu}></div> 

{/if}

{#if interruptOpen}

    <div class="modal-backdrop" onclick={(e) => { if (e.target === e.currentTarget) cancelInterrupt(); }}> 
      <div class="modal" role="dialog" aria-modal="true" aria-label="Interrupt Run"> 
        <header class="modal-header">
          <div class="title">Interrupt Run</div>
        </header> 
        <section class="modal-body"> 
          <div class="field"> 
            <label class="lbl">Session ID</label> 
            <input type="text" value={menuRun?.session_id || ''} readonly class="input readonly" /> 
          </div> 
          <div class="field"> <label class="lbl">Guidance</label> 
            <textarea rows="4" class="input" placeholder="Provide additional guidance…" bind:value={guidanceText}></textarea> 
          </div> 
          {#if interruptError}<div class="alert err">{interruptError}</div>{/if} 
        </section> 
        <footer class="modal-actions"> 
          <button 
            class="btn secondary" 
            type="button" 
            onclick={cancelInterrupt} 
            disabled={interruptBusy}>Cancel
          </button> 
          <button 
            class="btn primary" 
            type="button" 
            onclick={confirmInterrupt} 
            disabled={interruptBusy || !guidanceText.trim()}
            > 
            {interruptBusy ? 'Sending…' : 'OK'} 
          </button> 
        </footer> 
      </div> 
    </div> 
{/if} 

{#each liveWindows as w (w.id)}
<LiveRunWindow
id={w.id}
title={`Live Run: ${w.agent_id} / ${w.session_id}`}
run={{ agent_id: w.agent_id, session_id: w.session_id }}
z={z + 1}
onFocus={() => {}}
onRequestClose={() => closeLiveRun(w.id)}
/>
{/each}

<style> 
  .runs-root { display: grid; grid-template-rows: auto 1fr; gap: 10px; height: 100%; } 
  .toolbar { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; } 
  .filters { display: flex; gap: 12px; flex-wrap: wrap; align-items: end; } 
  .field { display: grid; gap: 6px; } 
  .field label { font-size: 12px; color: #6b7280; } 
  input[type="text"], select { 
    padding: 8px 10px; 
    border: 1px solid #d1d5db; 
    border-radius: 8px; 
    outline: none; 
    transition: border-color 120ms, box-shadow 120ms; 
  } 
  input[type="text"]:focus, select:focus { 
    border-color: #2563eb; 
    box-shadow: 0 0 0 3px rgba(37,99,235,0.16); 
  } 
  .actions { display: flex; gap: 8px; } 
  .actions button { 
    padding: 8px 12px; 
    border-radius: 8px; 
    border: 1px solid #d1d5db; background: #667dc6; cursor: pointer; 
  } 
  .actions button:hover { background: #183681; border-color: #c7d2fe; } 
  .loading, .empty, .err { padding: 10px; } .err { color: #b91c1c; } 
  .table-wrap { overflow: auto; } table.runs-table { 
    width: 100%; 
    border-collapse: separate; 
    border-spacing: 0; 
    border: 1px solid #e5e7eb; 
    border-radius: 10px; 
    background: #fff; 
  } 
  thead th { 
    background: #5d8ef0; 
    position: sticky; 
    top: 0; 
    z-index: 1; 
    padding: 8px 10px; 
    text-align: left; 
    cursor: pointer; 
    border-bottom: 1px solid #e5e7eb; 
  } 
  thead th.selected { color: #1d4ed8; } 
  tbody td { padding: 8px 10px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; } 
  tbody tr { 
    background: #b4b9c4; 
    position: sticky; 
    top: 0; z-index: 1; 
    padding: 8px 10px; 
    text-align: left; 
    cursor: default; 
    border-bottom: 1px solid #de6712; 
  } 
  .row-actions { text-align: right; } 
  .action-btn { 
    padding: 6px 10px; 
    border-radius: 8px; 
    border: 1px solid #d1d5db; 
    background: #9399eb; 
    cursor: pointer; 
  } 
  
  .action-btn:hover { background: #2651bc; } 
  .status.succeeded { color: #0f766e; font-weight: 600; } 
  .status.stopped { color: #b91c1c; font-weight: 600; } 
  .status.running { color: #2563eb; font-weight: 600; } 
  /* Popover menu (mirrors AgentsListWindow styling) */ 
  .popover-menu { 
    position: fixed; 
    z-index: 1000; 
    background: #938ae7; 
    border: 1px solid #ddd; 
    border-radius: 8px; 
    box-shadow: 0 4px 16px rgba(0,0,0,0.12); 
    padding: 6px 0; 
    min-width: 220px; 
    font-size: 1em; 
  } 
  .pmenu-label { 
    padding: 8px 18px; 
    color: #0f172a; 
    font-weight: 600; 
    border-bottom: 1px solid rgba(0,0,0,0.06); 
    background: rgba(255,255,255,0.4); 
  } 
  .pmenu-btn { 
    display: block; 
    width: 100%; 
    text-align: left; 
    border: none; 
    background: none; 
    padding: 8px 18px; 
    cursor: pointer; 
  } 
  .pmenu-btn:hover { background: #2957b3; color: #fff; } 
  .pmenu-btn.danger { color: #b91c1c; } 
  .backdrop { position: fixed; inset: 0; background: transparent; z-index: 999; } 
  /* Interrupt modal (mirrors AgentLaunchModal styling) */ 
  :root { --accent: var(--fi-accent, #2563eb); 
  --text: #0f172a; --muted: #64748b; --border: #e5e7eb; --subtle: #f8fafc; --radius: 12px; } 
  .modal-backdrop { 
    position: fixed; 
    inset: 0; 
    background: rgba(234, 227, 227, 0.35); 
    backdrop-filter: blur(4px); 
    display: grid; 
    place-items: center; 
    z-index: 2000; 
    padding: 16px; 
  } 
  .modal { 
    width: min(560px, 92vw); 
    max-height: calc(100vh - 32px); 
    display: grid; 
    grid-template-rows: auto 1fr auto; 
    background: #1c1b1b; border: 1px solid var(--border); 
    border-radius: var(--radius); 
    box-shadow: 0 18px 48px rgba(0,0,0,0.22); 
    overflow: hidden; color: var(--text); 
  } 
  .modal-header { 
    padding: 14px 16px; 
    background: linear-gradient(180deg, color-mix(in oklab, var(--accent) 96%, #fff 0%), var(--accent)); 
    color: #fff; 
    border-bottom: 1px solid color-mix(in oklab, var(--accent) 20%, #000 0%); 
  } 
  .modal-header .title { font-weight: 800; letter-spacing: 0.2px; } 
  .modal-body { padding: 14px 16px; display: grid; gap: 14px; overflow-y: auto; background: #ebe8e8; } 
  .lbl { font-size: 12px; font-weight: 700; color: #334155; letter-spacing: 0.02em; } 
  .input { 
    width: 100%; 
    padding: 10px 12px; border: 1px solid var(--border); 
    border-radius: 10px; 
    background: #faf6f6; 
    color: var(--text); 
    outline: none; 
    transition: border-color 120ms, box-shadow 120ms, background-color 120ms; 
    box-shadow: inset 0 1px 0 rgba(0,0,0,0.03); 
  } 
  .input.readonly { 
    background: #f5f7f9; 
    color: #475569; 
  } 
  textarea.input { 
    resize: vertical; 
    min-height: 82px; 
  } 
  .modal-actions { 
    display: flex; 
    justify-content: flex-end; 
    gap: 10px; 
    padding: 12px 16px; 
    border-top: 1px solid var(--border); 
    background: #fafafa; 
  } 
  .btn { 
    padding: 9px 14px; 
    border-radius: 10px; 
    font-weight: 700; 
    cursor: pointer; 
    border: 1px solid #cbd5e1; 
    background: #fff; color: var(--text); 
    transition: filter 120ms ease, transform 80ms ease, box-shadow 120ms ease, background 120ms ease, border-color 120ms ease; 
  } 
  .btn.primary { 
    border-color: color-mix(in oklab, var(--accent) 80%, #1d4ed8); 
    background: var(--accent); 
    color: #fff; box-shadow: 0 2px 8px color-mix(in oklab, var(--accent) 30%, #000 0%); 
  } 
  .btn.primary:hover { filter: brightness(1.05); } 
  .btn.secondary { background: #fff; } 
  .btn:disabled { opacity: 0.7; cursor: not-allowed; } 
  .alert.err { 
    color: #7f1d1d; 
    background: #fef2f2; 
    border: 1px solid #fee2e2; 
    padding: 10px 12px; 
    border-radius: 10px; 
  } 
</style>
