<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Agent Runs', 
        position = $bindable({ x: 140, y: 120 }), 
        size = $bindable({ w: 900, h: 520 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, 
        // optional initial filters
        filters = $bindable({ agent_id: '', status: '', q: '' }) 
    } = $props(); 
    let loading = $state(false); 
    let error = $state(null); 
    let runs = $state([]); 
    let sortBy = $state('created_at');
    let sortDir = $state('desc'); // 'asc' | 'desc' 
    let expanded = $state(null); // run id to show JSON details 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    function fmtDate(d) { if (!d) return ''; try { const dt = typeof d === 'string' || typeof d === 'number' ? new Date(d) : d; if (Number.isNaN(dt.getTime())) return String(d); return dt.toLocaleString(); } catch { return String(d); } } 
    function calcDurationMs(start, end) { const s = start ? new Date(start).getTime() : NaN; const e = end ? new Date(end).getTime() : NaN; if (!Number.isFinite(s) || !Number.isFinite(e)) return null; return Math.max(0, e - s); } 
    function fmtDuration(ms) { if (ms == null) return ''; const sec = Math.floor(ms / 1000); const h = Math.floor(sec / 3600); const m = Math.floor((sec % 3600) / 60); const s = sec % 60; if (h) return `${h}h ${m}m ${s}s`; if (m) return `${m}m ${s}s`; return `${s}s`; } 




  // NEW helpers
  function toInt(v, fallback = null) { 
    const n = Number(v); 
    return Number.isFinite(n) ? Math.trunc(n) : fallback; 
  } 
  function ensureJSONString(v) { 
    if (v == null) return null; 
    if (typeof v === 'string') return v; 
    try { 
      return JSON.stringify(v); 
    } catch { return String(v); } 
  } 
  // UPDATE normalizeRun to match AGENT_STEPS_SCHEMA and keep compat fields 
  function normalizeRun(r) { 
    // Primary fields (schema-aligned) 
//    const id = r.id ?? r.run_id ?? r.runId ?? ''; 
    const agent_id = r.agent_id ?? r.agentId ?? ''; 
    const created_at = r.created_at ?? r.last_updated ?? r.started_at ?? r.start_time ?? r.started ?? r.startTime ?? r.timestamp ?? null; 
    const session_id = r.session_id ?? r.sessionId ?? null; 
    const iteration = toInt(r.iteration, 0); 
  //  const step_token = r.step_token ?? r.stepToken ?? null; const next_step_token = r.next_step_token ?? r.nextStepToken ?? null; 
    const status = r.status ?? r.step_status ?? r.result_status ?? null; 
    // do NOT alias from r.state (that’s JSON per schema) 
   // const text = r.text ?? r.message ?? r.output ?? null; 
  //  const data = ensureJSONString(r.data); 
  //  const state = ensureJSONString(r.state); 
  //  const guidance = ensureJSONString(r.guidance); 
  //  const notes = r.notes ?? null; 
    // latency_ms: prefer provided, else derive when possible 
    let latency_ms = toInt(r.latency_ms, null); 
    const finished_raw = r.finished_at ?? r.end_time ?? r.ended ?? r.endTime ?? r.completed_at ?? null; 
    if (latency_ms == null && created_at && finished_raw) { 
      const s = new Date(created_at).getTime(); 
      const e = new Date(finished_raw).getTime(); 
      if (Number.isFinite(s) && Number.isFinite(e)) 
        latency_ms = Math.max(0, e - s); 
    } 
    const error = r.error ?? r.err ?? null; 
    // Back-compat fields for current table/sorting 
    const run_id = id; 
    const started_at = created_at ?? null; 
    const finished_at = finished_raw; 
    const duration_ms = latency_ms != null ? latency_ms : 0;


    return { ...r, // schema fields 
      id, created_at, agent_id, session_id, iteration,  status, latency_ms, error, 
      // compat fields for existing UI 
      run_id, started_at, finished_at, duration_ms 
      }; 
  }

  async function refresh() { 
      loading = true; 
      error = null; 
      try { 
        const params = new URLSearchParams(); 
        if (filters.agent_id) 
          params.set('agent_id', filters.agent_id); 
        if (filters.status) 
          params.set('status', filters.status); 
        if (filters.q) params.set('q', filters.q); 
        const url = 'http://127.0.0.1:5000/api/list-sessions-for-agent' + (params.toString() ? `?${params.toString()}` : ''); 

        const res = await fetch(url); 
        if (!res.ok) 
          throw new Error(`Server error: ${res.status}`); 
        const data = await res.json(); 
        runs = Array.isArray(data) ? data.map(normalizeRun) : []; sortNow(); 
      } catch (e) { error = e.message || String(e); } loading = false; }


    function sortNow() { const dir = sortDir === 'asc' ? 1 : -1; const key = sortBy; const sorted = [...runs].sort((a, b) => { const va = a[key]; const vb = b[key]; if (va == null && vb == null) return 0; if (va == null) return 1; if (vb == null) return -1; if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir; const sa = String(va); const sb = String(vb); return sa.localeCompare(sb) * dir; }); runs = sorted; } 
    function setSort(col) { if (sortBy === col) { sortDir = sortDir === 'asc' ? 'desc' : 'asc'; } else { sortBy = col; sortDir = 'desc'; } sortNow(); } 
    function exportCSV() { const cols = ['run_id', 'agent_id', 'status', 'started_at', 'finished_at', 'duration_ms']; const header = cols.join(','); const lines = runs.map(r => cols.map(c => { const v = r[c]; const s = v == null ? '' : String(v).replace(/"/g, '""'); return `"${s}"`; }).join(',') ); const blob = new Blob([header + '\n' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = 'agent_runs.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); } 


    // helpers for details + 
    function dash(v) {  return v == null || v === '' ? '—' : v;  } 
    function tryParseJSON(s) {  if (typeof s !== 'string') return null;  try { return JSON.parse(s); } catch { return null; }  } 
    function prettyJSONorRaw(s) {  const obj = tryParseJSON(s);  return obj ? JSON.stringify(obj, null, 2) : s ?? '';  } 
    function hasJSON(s) {  return typeof s === 'string' && tryParseJSON(s) != null;  }




    $effect(() => { refresh(); }); 
    // initial 
    $effect(() => { JSON.stringify(filters); refresh(); }); // refetch on filters change 
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
<section class="runs-root">
<div class="toolbar">
<div class="filters">
<div class="field">
<label>Agent ID</label>
<input type="text" placeholder="e.g. agent-123" bind:value={filters.agent_id} />
</div>
<div class="field">
<label>Status</label>
<select bind:value={filters.status}>
<option value="">Any</option>
<option value="running">running</option>
<option value="succeeded">succeeded</option>
<option value="failed">failed</option>
<option value="stopped">stopped</option>
</select>
</div>
<div class="field">
<label>Search</label>
<input type="text" placeholder="run id, text…" bind:value={filters.q} />
</div>
</div>
<div class="actions">
<button type="button" onclick={refresh} title="Refresh">⟳ Refresh</button>
<button type="button" onclick={exportCSV} title="Export CSV">⇩ Export CSV</button>
</div>
</div>

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
              <th onclick={() => setSort('started_at')} class:selected={sortBy==='started_at'}>Session Id</th>
              <th onclick={() => setSort('created_at')} class:selected={sortBy==='created_at'}>Last Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each runs as r}
              <tr>
                <td>{r.agent_id}</td>
                <td class={'status ' + (r.status || '').toLowerCase()}>{r.status}</td>
                <td>{r.session_id}</td>
                <td>{r.created_at}</td>
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

<style> 
    .runs-root { 
        display: grid; 
        grid-template-rows: auto 1fr; 
        gap: 10px; height: 100%; 
    } 
    .toolbar { 
        display: flex; 
        justify-content: space-between; 
        align-items: flex-end; 
        gap: 12px; 
    } 
    .filters { 
        display: flex; 
        gap: 12px; 
        flex-wrap: wrap; 
        align-items: end; 
    } 
    .field { 
        display: grid; 
        gap: 6px; 
    } 
    .field label { 
        font-size: 12px; 
        color: #6b7280; 
    } 
    input[type="text"], select { 
        padding: 8px 10px; 
        border: 1px solid #d1d5db; 
        border-radius: 8px; 
        outline: none; 
        transition: border-color 120ms, 
        box-shadow 120ms; 
    } 
    input[type="text"]:focus, select:focus { 
        border-color: #2563eb; 
        box-shadow: 0 0 0 3px rgba(37,99,235,0.16); 
    } 
    .actions { display: flex; gap: 8px; } 
    .actions button { 
        padding: 8px 12px; 
        border-radius: 8px; 
        border: 1px solid #d1d5db; 
        background: #667dc6; cursor: pointer; 
    } 
    .actions button:hover { 
        background: #183681; 
        border-color: #c7d2fe; 
    } 
    .loading, .empty, .err { padding: 10px; } .err { color: #b91c1c; } .table-wrap { overflow: auto; } 
    table.runs-table { 
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
    thead th.selected { 
        color: #1d4ed8; 
    } 
    tbody td { 
        padding: 8px 10px; 
        border-bottom: 1px solid #f3f4f6; 
        vertical-align: middle; 
    } 

    tbody tr {
      background: #b4b9c4;
        position: sticky; 
        top: 0; 
        z-index: 1; 
        padding: 8px 10px; 
        text-align: left; 
        cursor: pointer; 
        border-bottom: 1px solid #de6712; 
    }

     
    .row-actions { text-align: right; } 
    .row-actions button { 
        padding: 6px 10px; 
        border-radius: 8px; 
        border: 1px solid #d1d5db; 
        background: #2bf3a3; 
    } 
    .row-actions button:hover { background: #f1f5ff; } 
    .expanded td { background: #fbfdff; } 
    .json { 
        background: #0b1020; 
        color: #d1e7ff; 
        padding: 10px; 
        border-radius: 10px; 
        font-size: 12px; overflow: auto; 
    } 
    .status.succeeded { 
        color: #0f766e; 
        font-weight: 600; 
    } 
    .status.stopped { color: #b91c1c; font-weight: 600; } 
    .status.running { color: #2563eb; font-weight: 600; } 


    .details-grid {  
      display: grid;  
      grid-template-columns: 180px 1fr;  
      gap: 6px 12px;  
      padding: 10px 12px;  
    }  
    .details-grid .label { 
      color: #6b7280;  font-size: 12px;
      align-self: start;  
    }  
    .details-grid .value { 
      color: #0f172a;  
      white-space: pre-wrap;  
      word-break: break-word;  
    }  
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; } 
    .json {  
      background: #0b1020;  
      color: #d1e7ff;  
      padding: 8px 10px;  
      border-radius: 8px; 
      font-size: 12px; 
      overflow: auto;  
    } 
    .json.parsed { box-shadow: inset 0 0 0 1px rgba(37,99,235,0.25); }  
    .err-text { color: #b91c1c; background: #fff1f1; padding: 6px 8px; border-radius: 6px; } 




</style>
