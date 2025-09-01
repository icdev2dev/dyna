<script> 
    import ConversationsWindow from '../ConversationsWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z) 
    } = $props(); 
</script>
<ConversationsWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
onFocus={onFocus}
onRequestClose={onRequestClose}
/>
