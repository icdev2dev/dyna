<script> 
    import RunDetailWindow from '../RunDetailWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z) 
    } = $props(); 
</script>

<RunDetailWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
run={w.run}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>
