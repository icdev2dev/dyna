<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Conversations', 
        position = $bindable({ x: 40, y: 60 }), 
        size = $bindable({ w: 320, h: 560 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    
    let loading = $state(false); 
    let error = $state(null); 
    let tab = $state('all'); 
    // all | active | ended 
    let q = $state(''); 
    let conversations = $state([]); 
    let selectedId = $state(null)
    let rootEl = null; 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); } 
    async function refresh() { 
        loading = true; 
        error = null; 
        try { 
            const params = new URLSearchParams(); 
            if (tab !== 'all') params.set('status', tab); 
            if (q.trim()) params.set('q', q.trim()); 
            const res = await fetch('http://127.0.0.1:5000/api/conversations' + (params.toString() ? `?${params.toString()}` : '')); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); conversations = Array.isArray(data) ? data : []; 
        } catch (e) { error = e.message || String(e); } 
        finally { loading = false; } 
    } 
    $effect(() => { refresh(); }); 
    $effect(() => { tab; q; refresh(); }); 
    function fmtDate(d) { 
        if (!d) return ''; 
        try { 
            return new Date(d).toLocaleTimeString(); 
        } catch { return String(d); } 
    } 



    function openConversation(conv) { 
        try { rootEl?.dispatchEvent( new CustomEvent('openConversation', 
{ detail: { conversation_id: conv.id, title: conv.title ?? 'Conversation' }, bubbles: true, composed: true }) ); 
            } catch {} 
    } 
</script>

<WindowFrame
    id={id}
    title={title}
    bind:position
    bind:size
    {z}
    onFocus={onFocusCb}
    onRequestClose={requestClose} >

    {#snippet children()}

        <section 
            bind:this={rootEl} 
            class="conv-root"> 
            <div class="tabs"> 
                <button class:active={tab==='all'} onclick={() => (tab = 'all')}>All</button> 
                <button class:active={tab==='active'} onclick={() => (tab = 'active')}>Active</button> 
                <button class:active={tab==='ended'} onclick={() => (tab = 'ended')}>Ended</button> 
                <input class="search" type="text" placeholder="Search…" bind:value={q} /> 
            </div>

            {#if loading}
                <div class="status">Loading…</div>
            {:else if error}
                <div class="status err">{error}</div>
            {:else}
                <ul class="list"> 
                    {#each conversations as c (c.id)} 
                        <li 
                        class="row" 
                        class:selected={selectedId === c.id} 
                        onclick={() => { selectedId = c.id; openConversation(c); }} > 
                            <div class="title">{c.title ?? '(untitled)'}</div> 
                            <div class="meta">{fmtDate(c.updated_at ?? c.last_updated)}</div> 
                            <div class="preview">{c.preview ?? ''}</div> 
                        </li> 
                    {/each} 
                    {#if conversations.length === 0} 
                        <li class="empty">No conversations.</li> 
                    {/if} 
                </ul>
        {/if}
        </section> 
    {/snippet} 
</WindowFrame> 

<style> 
    .conv-root { 
        display: grid; 
        grid-template-rows: 1fr, top 0; 
        height: 100%; 
        /* tweak as desired */ 
        --row-h: 72px; 
        --row-gap: 8px; 
    }
    
    .tabs { display: grid; grid-template-columns: auto auto auto 1fr; gap: 8px; align-items: center; } 
    .tabs button { padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 8px; background: #c3bcbc; } 
    .tabs button.active { background: #565758; border-color: #93b0ff; font-weight: 700; } 
    .tabs .search { justify-self: end; min-width: 50px; padding: 8px 2px; border: 1px solid #d1d5db; border-radius: 8px; }


    .list { 
        list-style: none; 
        padding: 0; 
        margin: 6px 0 0; 
        overflow: auto; 
        /* use fixed vertical gap only */ 
        display: grid;
        background: #f7f7f7;  
        row-gap: var(--row-gap); 
        column-gap: 0;  
        grid-auto-rows: var(--row-h);
        /* Keep tracks packed at the top on resize */
        place-content: start; 
/*         align-content: start; or: place-content: start; */
    } 


    .row { 
        display: grid; 
        grid-template-columns: 1fr auto; 
        gap: 4px 10px; 
        background: #f7f7f7; 
        border: 1px solid #f7f7f7; 
        /* border-radius: 10px; */ 
        padding: 10px; 
        cursor: pointer; 
        /* fixed height for each row  
        height: var(--row-h); 
        */
        box-sizing: border-box; 
        overflow: hidden; 
        /* pack the internal grid rows to the top (prevents vertical centering) */ 
        /* align-content: start; */ 
        position: relative; 
        /* for selection bar */ 
    } 
    .row:hover { background: #bebfc1; } 
    /* right-side selection bar */ 
    .row.selected::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;           /* moved to left */
        width: 3px;
        height: 100%;
        background: #2563eb;
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
    }



    /* ensure title is top-left aligned explicitly */ 
    .title { 
        color: #475569; 
        font-weight: 700; 
        text-align: left; 
        align-self: start; 
        justify-self: start; 
    } 
    .meta { 
        color: #475569; 
        font-size: 12px; 
    } 
    .preview { 
        grid-column: 1 / span 2; 
        color: #64748b; 
        font-size: 13px; 
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        align-self: start; 
        /* keep preview near the top as well */ 
    } 
    .empty { 
        color: #64748b; 
        padding: 10px; 
        text-align: center; 
        border: 1px dashed #cbd5e1; 
        border-radius: 10px; 
    } 
</style>
