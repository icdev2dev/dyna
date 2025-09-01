<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Agent Sessions', 
        conversationId = $bindable(''), 
        position = $bindable({ x: 960, y: 60 }), 
        size = $bindable({ w: 360, h: 560 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    let loading = $state(false); 
    let error = $state(null); 
    let sessions = $state([]); 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    async function refresh() { 
        if (!conversationId) return; 
        loading = true; error = null; 
        try { 
            const res = await fetch(`http://127.0.0.1:5000/api/conversation-sessions?conversation_id=${encodeURIComponent(conversationId)}`); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); 
            sessions = Array.isArray(data) ? data : []; 
        } catch (e) { error = e.message || String(e); } finally { loading = false; } 
    } 
    $effect(() => { conversationId; refresh(); }); 
    function badgeClass(s) { 
        const v = (s || '').toLowerCase(); 
        if (v === 'running') return 'badge running'; 
        if (v === 'paused') return 'badge paused'; 
        if (v === 'stopped') return 'badge stopped'; 
        return 'badge'; 
    } 
    async function post(path, body) { 
        const res = await fetch(`http://127.0.0.1:5000${path}`, 
                                { 
                                    method: 'POST', 
                                    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body ?? {}) 
                                }); 
        if (!res.ok) throw new Error(`HTTP ${res.status}`); 
    } 
    
    async function pause(s) { 
        try { 
            await post('/api/pause-agent', { session_id: s.session_id }); 
            await refresh(); 
        } catch (e) { alert(e.message || String(e)); } } 
    async function resume(s) { 
        try { 
            await post('/api/resume-agent', 
            { session_id: s.session_id }); await refresh(); } catch (e) { alert(e.message || String(e)); 
            
        } 
    } 
    
    async function stop(s) { 
        try { 
            await post('/api/stop-agent', { session_id: s.session_id }); 
            await refresh(); 
        } catch (e) { alert(e.message || String(e)); } 
    } 
    async function interrupt(s) { 
        const g = window.prompt('Guidance to interrupt with (optional):', ''); 
        if (g == null) return; 
        try { await post('/api/interrupt-agent', { session_id: s.session_id, guidance: g }); await refresh(); } catch (e) { alert(e.message || String(e)); } } 
    async function sendQuick(s) { 
        const msg = window.prompt('Send message to this agent:', ''); 
        if (!msg && msg !== '') return; 
        try { 
            await post('/api/send-to-agent', 
            { session_id: s.session_id, message: msg }); 
        } catch (e) { alert(e.message || String(e)); } } 
</script>

<WindowFrame
    id={id}
    title={title}
    bind:position
    bind:size
    {z}
    onFocus={onFocusCb}
    onRequestClose={requestClose} >

    {#snippet headerActions()}
        <div style="display:flex; gap:6px;">
        <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={refresh}>Refresh</button>
        <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
        </div>
    {/snippet}

    {#snippet children()}
        <section class="panel-root">
            {#if loading}
                <div>Loading…</div>
            {:else if error}
                <div class="err">Error: {error}</div>
            {:else}
                <div class="cards">
                {#each sessions as s (s.session_id)}
                    <div class="card">
                    <div class="card-head">
                    <div class="agent">{s.agent_name ?? s.agent_id ?? 'Agent'}</div>
                    <div class={badgeClass(s.status)}>{s.status ?? ''}</div>
                    </div>
                    <div class="sub">ID {s.session_id}</div>

                            <div class="lbl">Last output</div>
                            <div class="out">{s.last_output ?? '(idle)'}</div>

                            {#if Array.isArray(s.tags) && s.tags.length}
                                <div class="tags">
                                {#each s.tags as t}<span class="tag">{t}</span>{/each}
                                </div>
                            {/if}

                            <div class="row-btns">
                                {#if (s.status || '').toLowerCase() === 'running'}
                                    <button class="btn" onclick={() => pause(s)}>Pause</button>
                                    <button class="btn" onclick={() => interrupt(s)}>Interrupt</button>
                                    <button class="btn" onclick={() => sendQuick(s)}>Send</button>
                                    <button class="btn danger" onclick={() => stop(s)}>Stop</button>
                                {:else if (s.status || '').toLowerCase() === 'paused'}
                                    <button class="btn" onclick={() => resume(s)}>Resume</button>
                                    <button class="btn" onclick={() => sendQuick(s)}>Send</button>
                                {:else}
                                    <button class="btn" onclick={() => sendQuick(s)}>Send</button>
                                {/if}
                            </div>
                        </div>
                {/each}
                {#if !sessions.length}
                    <div class="empty">No sessions for this conversation.</div>
                {/if}
            </div>
        {/if}
        </section>
    {/snippet}
</WindowFrame>

<style> 
    .panel-root { height: 100%; overflow: auto; } 
    .cards { display: grid; gap: 10px; } 
    .card { border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px; background: #fff; } 
    .card-head { display: flex; justify-content: space-between; align-items: center; } 
    .agent { font-weight: 800; } 
    .badge { padding: 3px 8px; border-radius: 999px; background: #eef2ff; color: #1e3a8a; font-weight: 700; font-size: 12px; border: 1px solid #c7d2fe; } 
    .badge.running { background: #ecfeff; color: #0e7490; border-color: #99f6e4; } 
    .badge.paused { background: #fff7ed; color: #b45309; border-color: #fed7aa; } 
    .badge.stopped { background: #fee2e2; color: #991b1b; border-color: #fecaca; } 
    .sub { color: #64748b; font-size: 12px; margin-top: 2px; } 
    .lbl { margin-top: 8px; font-size: 12px; color: #475569; } 
    .out { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px; } 
    .tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; } 
    .tag { background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 999px; padding: 3px 8px; font-size: 12px; } 
    .row-btns { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; } 
    .btn { padding: 6px 10px; border: 1px solid #cbd5e1; border-radius: 8px; background: #fff; cursor: pointer; } 
    .btn.danger { color: #991b1b; border-color: #fecaca; background: #fee2e2; } 
    .empty { color: #64748b; text-align: center; padding: 10px; border: 1px dashed #cbd5e1; border-radius: 10px; } 
    .err { color: #b91c1c; } 
</style>

