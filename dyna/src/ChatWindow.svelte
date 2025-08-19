<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import ChatPanel from './ChatPanel.svelte'; 
    let { 
        id, 
        title = 'Chat', 
        messages = $bindable([]), 
        config = $bindable({}), 
        chatType = 'default',
        persist = 'keep', 
        position = $bindable({ x: 48, y: 48 }), 
        size = $bindable({ w: 520, h: 420 }), 
        z = 1, 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    function requestClose() { 
        const inFlight = messages.some(m => m.meta?.streaming); 
        if (inFlight && !window.confirm('A reply is still generating. Stop and close?')) return; 
        onRequestCloseCb?.({ id, isDirty: false, value: { messages, config }, persist }); 
    } 
</script>


<WindowFrame
    id={id}
    title={title}
    bind:position={position}
    bind:size={size}
    z={z}
    onFocus={onFocusCb}
    onRequestClose={requestClose} >
    {#snippet children()}
        <ChatPanel bind:messages={messages} config={config} chatType={chatType} />
    {/snippet}

    {#snippet headerActions()}
        <button
            class="win-close"
            type="button"
            onpointerdown={(e) => e.stopPropagation()}
            onclick={requestClose}
            aria-label="Close"
        >×</button>
    {/snippet}
</WindowFrame>
