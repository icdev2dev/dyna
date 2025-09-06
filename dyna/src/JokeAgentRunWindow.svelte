<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Launch Run — JokeAgent ---', 
        position = $bindable({ x: 80, y: 80 }), 
        size = $bindable({ w: 520, h: 360 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, 
        // optional seed 
        agentId = '', seedPrompt = '' 
    } = $props(); 
    let form = $state({ session_id: '', prompt: seedPrompt, config_json: '{\n}' }); 
    let loading = $state(false); 
    let error = $state(null); 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    async function launch() { 
        error = null; 
        loading = true; 
        try { 
            let cfg = {}; 
            if (form.config_json?.trim()) { 
                try { cfg = JSON.parse(form.config_json); } catch { throw new Error('Config must be valid JSON'); } 
            } 
            const res = await fetch('http://127.0.0.1:5000/api/create-agent', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ agent_id: agentId, session_id: form.session_id || undefined, input: form.prompt || '', config: cfg }) 
            }); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            // Optional: open runs right away 
            try { // Bubble an event Canvas already handles 
                window.dispatchEvent?.(new Event('noop')); 
                // no-op safeguard 
            } catch {} 
            // Ask Canvas to show runs 
            try { // Dispatch via our root; WindowFrame parent listens in Canvas layer 
                const root = document.querySelector('.windows'); 
                root?.dispatchEvent(new CustomEvent('showAgentRuns', { detail: { agent_id: agentId }, bubbles: true, composed: true })); 
            } catch {} requestClose(); 
        } catch (e) { error = e?.message || String(e); } finally { loading = false; } 
    } 
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
<div class="root">
<div class="grid">
<label class="lbl">Agent ID</label>
<input class="inp" type="text" value={agentId} readonly />

    <label class="lbl">Session ID (optional)</label>
    <input class="inp" type="text" bind:value={form.session_id} placeholder="auto if blank" />

    <label class="lbl">Prompt</label>
    <textarea class="inp" rows="4" bind:value={form.prompt} placeholder="What should the joke be about?"></textarea>

    <label class="lbl">Config (JSON, optional)</label>
    <textarea class="inp mono" rows="6" bind:value={form.config_json}></textarea>
  </div>

  {#if error}<div class="err">{error}</div>{/if}

  <div class="row">
    <button class="btn primary" onclick={launch} disabled={loading || !agentId}>
      {loading ? 'Launching…' : 'Launch'}
    </button>
    <button class="btn" onclick={requestClose} disabled={loading}>Cancel</button>
  </div>
</div>
{/snippet}
</WindowFrame>

<style> 
    .root { display: grid; gap: 10px; } 
    .grid { display: grid; gap: 8px; } 
    .lbl { font-size: 12px; font-weight: 700; color: #6b7280; } 
    .inp { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; outline: none; } 
    .inp:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.16); } 
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; } 
    .row { display: flex; gap: 8px; justify-content: flex-end; } 
    .btn { padding: 8px 12px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; } 
    .btn.primary { border-color: #1d4ed8; background: #2563eb; color:#fff; font-weight:700; } 
    .err { color: #b91c1c; } 
</style>