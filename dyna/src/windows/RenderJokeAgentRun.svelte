<script> 
    import JokeAgentRunWindow from '../JokeAgentRunWindow.svelte'; 
    let { 
        w, 
        onFocus, 
        onRequestClose, 
        position = $bindable(w.position), 
        size = $bindable(w.size), 
        z = $bindable(w.z) 
    } = $props(); 
</script>

<JokeAgentRunWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
agentId={w.agentId}
seedPrompt={w.seedPrompt}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>
