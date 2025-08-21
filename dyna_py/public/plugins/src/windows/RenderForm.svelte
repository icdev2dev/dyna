<script> 
    import FormWindow from '../FormWindow.svelte'; 
    export let w; 
    export let onFocus; 
    export let onRequestClose; 
    export let onSubmit; 
    export let transitions = true; 
</script>

<FormWindow
    id={w.id}
    title={w.title}
    schema={w.schema}
    bind:value={w.value}
    persist={w.persist}
    bind:position={w.position}
    bind:size={w.size}
    z={w.z}
    {transitions}
    onSubmit={onSubmit}
    onRequestClose={onRequestClose}
    onFocus={onFocus}
/>

