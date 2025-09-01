<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import ChatPanel from './ChatPanel.svelte'; 
    let { 
        id, 
        title = 'Conversation', 
        conversation = $bindable({ id: '', title: '' }), 
        position = $bindable({ x: 380, y: 60 }), 
        size = $bindable({ w: 560, h: 560 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    let loading = $state(false); 
    let error = $state(null); 
    let messages = $state([]); 
    let participants = $state([]); 
    function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: { messages }, persist }); } 
    async function refresh() { 
        if (!conversation?.id) return; 
        loading = true; 
        error = null; 
        try { 
            const res = await fetch(`http://127.0.0.1:5000/api/conversation-messages?conversation_id=${encodeURIComponent(conversation.id)}`); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); 
            messages = Array.isArray(data?.messages) ? data.messages : Array.isArray(data) ? data : []; 
            participants = Array.isArray(data?.participants) ? data.participants : (data?.participants ?? []); 
        } catch (e) { error = e.message || String(e); } finally { loading = false; } 
    } 
    $effect(() => { conversation?.id; refresh(); }); 
    function conversationChatAdapter(convId) { 
        // console.log(messages)

        return { 
            async *stream({ messages, config, signal }) { 
                const res = await fetch('http://127.0.0.1:5000/api/conversation-chat', 
                                        { 
                                            method: 'POST', 
                                            headers: { 'Content-Type': 'application/json' }, 
                                            body: JSON.stringify({ conversation_id: convId, messages, config }), 
                                            signal 
                                        }); 
                const reader = res.body.getReader();
            //    console.log(reader) 
                const td = new TextDecoder(); 
                while (true) { 
                    const { value, done } = await reader.read(); 
                    if (done) break; 
                    yield td.decode(value, { stream: true }); 
                } 
            } 
        };
    } 
</script>

<WindowFrame
    id={id}
    title={conversation.title || title}
    bind:position
    bind:size
    {z}
    onFocus={onFocusCb}
    onRequestClose={requestClose}
    >
    {#snippet headerActions()}
    <div style="display:flex; gap:6px;">
    <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={refresh}>Add Participants</button>

    <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={refresh}>Refresh</button>
    <button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
    </div>
    {/snippet}

    {#snippet children()}
        <section class="thread-root">
            <div class="head-row">
            <div class="participants">
            {#each participants as p}
                <span class="pill">{p.name ?? p.id ?? 'participant'}</span>
            {/each}
            {#if !participants?.length}
                <span class="muted">No participants info</span>
            {/if}
            </div>
            </div>

            {#if loading}
                <div>Loading…</div>
            {:else if error}
                <div class="err">Error: {error}</div>
            {:else}
                <div class="panel">
                    <ChatPanel bind:messages={messages} adapter={conversationChatAdapter(conversation.id)} />
                </div>
            {/if}
        </section>
    {/snippet}
</WindowFrame>

<style> 
    .thread-root { display: grid; grid-template-rows: auto 1fr; height: 100%; } 
    .head-row { padding-bottom: 6px; border-bottom: 1px solid #eef0f3; } 
    .participants { display: flex; gap: 6px; flex-wrap: wrap; } 
    .pill { 
        background: #e7efff; 
        color: #1e3a8a; 
        border: 1px solid #93b0ff; 
        padding: 4px 8px; 
        border-radius: 999px; 
        font-weight: 600; 
        font-size: 20px; 
    } 
    .muted { color: #64748b; font-size: 12px; } .panel { height: 100%; } .err { color: #b91c1c; } 
</style>
