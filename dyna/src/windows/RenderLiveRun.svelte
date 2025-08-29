<script> 
    import LiveRunWindow from '../LiveRunWindow.svelte'; 
    export let w; 
    export let onFocus; 
    export let onRequestClose; 
</script>
<LiveRunWindow
    id={w.id}
    title={w.title}
    bind:position={w.position}
    bind:size={w.size}
    z={w.z}
    persist={w.persist}
    run={w.run}
    onFocus={onFocus}
    onRequestClose={onRequestClose}
/>