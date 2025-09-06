<script> 
    import AgentConfigsWindow from '../AgentConfigsWindow.svelte'; 
    let { 
            w, 
            onFocus, 
            onRequestClose, 
            position = $bindable(w.position), 
            size = $bindable(w.size), 
            z = $bindable(w.z) 
        } = $props(); 
</script>
<AgentConfigsWindow
    id={w.id}
    title={w.title}
    bind:position
    bind:size
    bind:z
    onFocus={onFocus}
    onRequestClose={onRequestClose}
/>


