<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import MetadataInterpreter from './MetaDataInterpreter.svelte'; 
    let { 
        id, 
        title = 'Metadata Editor', 
        value = $bindable({ entities: [] }), 
        disabled = false, 
        readOnly = false, 
        persist = 'keep', 
        position = $bindable({ x: 60, y: 60 }), 
        size = $bindable({ w: 900, h: 620 }), 
        z = 1, 
        confirmOnDirtyClose = true, 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, 
        debug = false 
    } = $props(); 
    let isDirty = false; 
    let initialSnapshot = ''; 
    let lastId = null; 
    $effect(() => { if (id !== lastId) { lastId = id; initialSnapshot = JSON.stringify(value ?? {}); isDirty = false; } });

    $effect(() => { isDirty = JSON.stringify(value ?? {}) !== initialSnapshot; }); 
    function handleSubmit({ value: v }) { 
        initialSnapshot = JSON.stringify(v ?? {}); isDirty = false; 
    } 
    function requestClose() { 
        onRequestCloseCb?.({ id, isDirty, value, persist, confirmOnDirtyClose }); 
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
    <MetadataInterpreter bind:value={value} {disabled} {readOnly} onSubmit={handleSubmit} {debug} />
    {/snippet}

    {#snippet headerActions()}
    <div class="header-actions">
    <button type="button" class="win-close" onpointerdown={(e) => e.stopPropagation()} onclick={() => handleSubmit({ value })}>Save</button>
    <button type="button" class="win-close" onpointerdown={(e) => e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
    </div>
    {/snippet}
</WindowFrame>

<style> .header-actions { display: flex; gap: 6px; } </style>
