<script> 
    let { 
        open = $bindable(false), 
        agentId = '', 
        busy = $bindable(false), 
        submitError = $bindable(null), 
        onConfirm: onConfirmCb, onCancel: onCancelCb 
    } = $props(); 
    let form = $state({ session_id: '', prompt: '', config_json: '{\n}' }); 


    let localErr = $state(null); 
    // Reset inputs each time we open for a different agent 
    $effect(() => { if (open) { localErr = null; form = { session_id: '', prompt: '', config_json: '{\n}' }; } }); 
    function confirm() { 
        localErr = null; 
        let cfg = {}; 
        try { 
            cfg = form.config_json ? JSON.parse(form.config_json) : {}; 
        } catch { 
            localErr = 'Config must be valid JSON'; return; 
        } 
        onConfirmCb?.({ agent_id: agentId, session_id: form.session_id || undefined, prompt: form.prompt || undefined, config: cfg }); 
    } 
    function cancel() { if (busy) return; onCancelCb?.(); } 
</script>

{#if open}

    <div class="modal-backdrop" onclick={(e) => { if (e.target === e.currentTarget) cancel(); }}> <div class="modal" role="dialog" aria-modal="true" aria-label="Launch Agent" onkeydown={onKey} tabindex="0"> <header class="modal-header"> <div class="title">Launch Agent</div> </header>
    <section class="modal-body">
        <div class="field">
        <label class="lbl">Agent ID</label>
        <input type="text" value={agentId} readonly class="input readonly" />
        </div>

        <div class="field">
        <label class="lbl">Prompt / Input</label>
        <textarea
            rows="4"
            placeholder="Enter initial input for the agent"
            bind:value={form.prompt}
            class="input"
        ></textarea>
        <div class="hint">Tip: press Ctrl/⌘ + Enter to launch quickly</div>
        </div>

        {#if localErr}
        <div class="alert err">{localErr}</div>
        {/if}
        {#if submitError}
        <div class="alert err">{submitError}</div>
        {/if}
    </section>

    <footer class="modal-actions">
        <button type="button" class="btn secondary" onclick={cancel} disabled={busy}>Cancel</button>
        <button type="button" class="btn primary" onclick={confirm} disabled={busy}>
        {busy ? 'Launching…' : 'OK'}
        </button>
    </footer>
    </div>
    </div> 
{/if}


 <style> 
 /* Theme hooks (uses Canvas/WindowFrame accent if present) */ 
 :root { 
    --accent: var(--fi-accent, #2563eb); 
    --text: #0f172a; 
    --muted: #64748b; 
    --border: #e5e7eb; 
    --subtle: #f8fafc; 
    --radius: 12px; 
} 
.modal-backdrop { 
    position: fixed; 
    inset: 0; 
    background: rgba(15, 23, 42, 0.35); 
    backdrop-filter: blur(4px); display: grid; place-items: center; 
    z-index: 2000; 
    padding: 16px; 
} 
.modal { 
    width: min(560px, 92vw); 
    max-height: calc(100vh - 32px); 
    display: grid; 
    grid-template-rows: auto 1fr auto; 
    background: #fff; 
    border: 1px solid var(--border); 
    border-radius: var(--radius); 
    box-shadow: 0 18px 48px rgba(0,0,0,0.22); 
    overflow: hidden; 
    /* keep header/footer pinned */ 
    color: var(--text); 
} 
.modal-header { 
    padding: 14px 16px; 
    background: linear-gradient(180deg, color-mix(in oklab, var(--accent) 96%, #fff 0%), var(--accent)); 
    color: #fff; 
    border-bottom: 1px solid color-mix(in oklab, var(--accent) 20%, #000 0%); } .modal-header .title { font-weight: 800; letter-spacing: 0.2px; } .modal-body { padding: 14px 16px; display: grid; gap: 14px; overflow-y: auto; /* vertical scroll only when needed */ overflow-x: hidden; /* avoid horizontal scrollbar strip */ background: #fff; } .field { display: grid; gap: 6px; } .lbl { font-size: 12px; font-weight: 700; color: #334155; letter-spacing: 0.02em; } .hint { font-size: 12px; color: var(--muted); margin-top: 2px; } .input { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: #fff; /* clean surface */ color: var(--text); outline: none; transition: border-color 120ms, box-shadow 120ms, background-color 120ms; box-shadow: inset 0 1px 0 rgba(0,0,0,0.03); } .input::placeholder { color: #9ca3af; } .input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px color-mix(in oklab, var(--accent) 24%, #fff 0%); } .input.readonly { background: #f9fafb; color: #475569; } textarea.input { resize: vertical; /* allow height resize; no unexpected scrollbars */ min-height: 82px; } .modal-actions { display: flex; justify-content: flex-end; gap: 10px; padding: 12px 16px; border-top: 1px solid var(--border); background: #fafafa; } .btn { padding: 9px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; border: 1px solid #cbd5e1; background: #fff; color: var(--text); transition: filter 120ms ease, transform 80ms ease, box-shadow 120ms ease, background 120ms ease, border-color 120ms ease; } .btn:hover { background: #f8fafc; } .btn:active { transform: translateY(1px); } .btn:disabled { opacity: 0.7; cursor: not-allowed; } .btn.primary { border-color: color-mix(in oklab, var(--accent) 80%, #1d4ed8); background: var(--accent); color: #fff; box-shadow: 0 2px 8px color-mix(in oklab, var(--accent) 30%, #000 0%); } .btn.primary:hover { filter: brightness(1.05); } .btn.secondary { background: #fff; } .alert.err { color: #7f1d1d; background: #fef2f2; border: 1px solid #fee2e2; padding: 10px 12px; border-radius: 10px; } </style>
