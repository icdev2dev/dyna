<script> 
    import ConversationThreadWindow from '../ConversationThreadWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z) 
    } = $props(); 
</script>
<ConversationThreadWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
conversation={w.conversation}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>