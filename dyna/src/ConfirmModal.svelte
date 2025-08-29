<script> 
    let { 
        open = $bindable(false), 
        title = 'Confirm', message = '', 
        okLabel = 'OK', 
        cancelLabel = 'Cancel', 
        busy = $bindable(false), 
        onConfirm: 
        onConfirmCb, 
        onCancel: onCancelCb 
    } = $props(); 
    
    function confirm() { if (!busy) onConfirmCb?.(); } 
    function cancel() { if (!busy) onCancelCb?.(); } 
</script>


{#if open}
    <div 
        class="modal-backdrop" 
        onclick={(e) => { if (e.target === e.currentTarget) cancel(); }}> 
        <div 
            class="modal" 
            role="dialog" 
            aria-modal="true" 
            aria-label={title}> 
            <header class="modal-header"> 
                <div class="title">{title}</div> 
            </header>
            <section class="modal-body">
                <div class="msg">{message}</div>
            </section>

            <footer class="modal-actions">
                <button type="button" class="btn secondary" onclick={cancel} disabled={busy}>{cancelLabel}</button>
                <button type="button" class="btn primary" onclick={confirm} disabled={busy}>{busy ? 'Working…' : okLabel}</button>
            </footer>
        </div>
    </div> 
{/if} 

<style> 
    :root { --accent: var(--fi-accent, #2563eb); --text:#0f172a; --border:#e5e7eb; --radius:12px; } 
    .modal-backdrop { 
        position:fixed; 
        inset:0; 
        background:rgba(15,23,42,0.35); 
        backdrop-filter:blur(4px); 
        display:grid; 
        place-items:center; 
        z-index:2000; 
        padding:16px; 
    } 
    .modal { 
        width:min(560px,92vw); 
        display:grid; 
        grid-template-rows:auto 1fr auto; 
        background:#fff; 
        border:1px solid var(--border); 
        border-radius:var(--radius); 
        box-shadow:0 18px 48px rgba(0,0,0,0.22); 
        overflow:hidden; 
        color:var(--text); 
    } 
    
    .modal-header { 
        padding:14px 16px; 
        background:linear-gradient(180deg, color-mix(in oklab, var(--accent) 96%, #fff 0%), var(--accent)); 
        color:#fff; 
    } 
    .modal-header 
    .title { font-weight:800; } 
    .modal-body { padding:14px 16px; } 
    .msg { white-space:pre-wrap; } 
    .modal-actions { 
        display:flex; 
        justify-content:flex-end; 
        gap:10px; 
        padding:12px 16px; 
        border-top:1px solid var(--border); 
        background:#fafafa; 
    } 
    .btn { 
        padding:9px 14px; 
        border-radius:10px; 
        font-weight:700; 
        cursor:pointer; 
        border:1px solid #cbd5e1; 
        background:#fff; 
    } 
    
    .btn.primary { 
        border-color:#1d4ed8; 
        background:var(--accent); color:#fff; 
        box-shadow:0 2px 8px rgba(37,99,235,0.25); 
    } 
    .btn.primary:hover { 
        filter:brightness(1.05); 
    } 
.btn.secondary { background:#fff; } .btn:disabled { opacity:.7; cursor:not-allowed; }
</style>

<!--

Use it where you need the specialized message

<script> 
    import ConfirmModal from './ConfirmModal.svelte'; 
    // ... 
    let pauseOpen = $state(false); 
    let pauseBusy = $state(false); 
    let pauseTarget = $state({ agent_id: '', session_id: '' }); 
    let pauseErr = $state(null); 
    function openPause(run) { 
        pauseTarget = { agent_id: run.agent_id, session_id: run.session_id }; 
        pauseErr = null; 
        pauseOpen = true; 
    } 
    async function confirmPause() { 
        pauseBusy = true; 
        pauseErr = null; 
        try { // Placeholder call; wire to your API later: // 
            await fetch('http://127.0.0.1:5000/api/pause-session', 
                { // method: 'POST', 
                // headers: { 'Content-Type': 'application/json' }, 
                // body: JSON.stringify(pauseTarget) // 
            }); 
            alert(`Would pause session ${pauseTarget.session_id} of agent ${pauseTarget.agent_id}`); 
            pauseOpen = false; 
        } catch (e) { pauseErr = e.message || String(e); } finally { pauseBusy = false; } 
    } 
    
    function cancelPause() { if (pauseBusy) return; pauseOpen = false; } 
</script>


Somewhere in your UI (e.g., an Actions popover), call openPause(r) to show the modal.

Place the modal once at the bottom of the component:

<ConfirmModal
    open={pauseOpen}
    bind:busy={pauseBusy}
    title="Confirm Pause"
    message={You are about to pause the session ${pauseTarget.session_id} of agent ${pauseTarget.agent_id}.}
    okLabel="Pause"
    cancelLabel="Cancel"
    onConfirm={confirmPause}
    onCancel={cancelPause}
/>

Notes

The message prop is just a string; use template literals to inject agent_id/session_id for bespoke messaging.
The modal style matches your existing AgentLaunchModal for visual consistency.
You can reuse this ConfirmModal for delete confirmations or any OK/Cancel need by changing title/message/okLabel.



-->