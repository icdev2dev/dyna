<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Last Updated', 
        position = $bindable({ x: 120, y: 120 }), 
        size = $bindable({ w: 700, h: 480 }), 
        z = $bindable(1), 
        persist = 'keep', 
        // run = { agent_id, session_id } 
        run = $bindable({ agent_id: '', session_id: '' }), 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    let loading = $state(false); 
    let error = $state(null); 
    let last = $state({ last_text: '', timestamp: null }); 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    function fmtDate(d) { if (!d) return ''; try { const dt = new Date(d); if (Number.isNaN(dt.getTime())) return String(d); return dt.toLocaleString(); } catch { return String(d); } } 
    async function refresh() { 
        if (!run?.agent_id || !run?.session_id) return; 
        loading = true; 
        error = null; 
        try { 
            // Placeholder API (backend to implement) 
            const params = new URLSearchParams({ agent_id: String(run.agent_id), session_id: String(run.session_id) }); 
            const url = `http://127.0.0.1:5000/api/run-last-updated?${params.toString()}`; 
            const res = await fetch(url); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); 
            last = { last_text: data.last_text ?? '', timestamp: data.timestamp ?? null }; 
        } catch (e) { error = e.message || String(e); } 
        loading = false; 
    } 
        // Auto load when agent/session changes 
    $effect(() => { if (run?.agent_id && run?.session_id) refresh(); }); 
</script>
<WindowFrame
id={id}
title={title}
bind:position
bind:size
z={z}
onFocus={onFocusCb}
onRequestClose={requestClose}>

{#snippet headerActions()}
<div style="display:flex; gap:6px;">
<button class="win-close" type="button" onpointerdown={(e) => e.stopPropagation()} onclick={refresh}>Refresh</button>
<button class="win-close" type="button" onpointerdown={(e) => e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
</div>
{/snippet}

{#snippet children()}
<section class="detail-root">
<div class="meta">
<div><strong>Agent ID:</strong> {run.agent_id}</div>
<div><strong>Session ID:</strong> {run.session_id}</div>
<div><strong>Last updated:</strong> {fmtDate(last.timestamp)}</div>
</div>

  {#if loading}
    <div>Loading…</div>
  {:else if error}
    <div class="err">Error: {error}</div>
  {:else}
    <div class="content">
      <label>Last updated text</label>
      <pre class="mono box">{last.last_text || ''}</pre>
    </div>
  {/if}
</section>
{/snippet}
</WindowFrame>

<style> 
    .detail-root { display: grid; gap: 12px; height: 100%; } 
    .meta { display: grid; gap: 6px; } 
    .content { display: grid; gap: 6px; } 
    label { font-size: 12px; color: #6b7280; } 
    .mono.box { 
        background: #0b1020; 
        color: #d1e7ff; 
        padding: 10px; 
        border-radius: 10px; 
        overflow: auto; 
        white-space: pre-wrap; 
        word-break: break-word; 
    } 
    .err { color: #b91c1c; } 
</style>
