<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import FormInterpreter from './FormInterpreter.svelte'; 
    let { 
        id, 
        title = 'Form', 
        schema = [], 
        value = $bindable({}), 
        disabled = false, 
        readOnly = false, 
        persist = 'destroy',  
        position = $bindable({ x: 48, y: 48 }), 
        size = $bindable({ w: 420, h: 280 }), 
        z = 1, transitions = true,
        confirmOnDirtyClose = true, 
        onSubmit: onSubmitCb, 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, 
        debug = false 
    } = $props(); 
    let isDirty = false; 
    let initialSnapshot = ''; 
    let lastId = null; 
    // Reset baseline only when the window id changes (or on mount) 
    $effect(() => { 
        if (id !== lastId) { 
            lastId = id; 
            initialSnapshot = JSON.stringify(value ?? {}); isDirty = false; 
        } 
    }); 
    $effect(() => { 
        const now = JSON.stringify(value ?? {}); 
        isDirty = now !== initialSnapshot; 
    }); 
    function handleSubmit({ value: v }) { 
        onSubmitCb?.({ id, value: v }); 
        initialSnapshot = JSON.stringify(value ?? {}); 
        isDirty = false; 
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
        <FormInterpreter
            {schema}
            bind:value={value}
            {disabled}
            {readOnly}
            onSubmit={handleSubmit}
            {debug}
            />
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
