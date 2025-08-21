<script> 
    import MetaDataWindow from '../MetaDataWindow.svelte'; 
    export let w; 
    export let onFocus; 
    export let onRequestClose; 
</script>

<MetaDataWindow
    id={w.id}
    title={w.title}
    bind:position={w.position}
    bind:size={w.size}
    z={w.z}
    persist={w.persist}
    bind:value={w.value}
    onFocus={onFocus}
    onRequestClose={onRequestClose}
/>
