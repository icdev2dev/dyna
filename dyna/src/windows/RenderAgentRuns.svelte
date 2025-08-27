<script> 
    import AgentRunsWindow from '../AgentRunsWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z), 
        persist = $bindable(w.persist), 
        filters = $bindable(w.filters) 
    } = $props(); 
</script>
<AgentRunsWindow
    id={w.id}
    title={w.title}
    bind:position
    bind:size
    bind:z
    bind:filters
    onFocus={onFocus}
    onRequestClose={onRequestClose}
/>