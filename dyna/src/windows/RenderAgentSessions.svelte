<script> 
    import AgentSessionsPanelWindow from '../AgentSessionsPanelWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z) 
    } = $props(); 
</script>

<AgentSessionsPanelWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
conversationId={w.conversationId}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>
