<script> 
    import ChatWindow from '../ChatWindow.svelte'; 
    export let w; 
    export let onFocus; 
    export let onRequestClose; 
</script>

<ChatWindow
    id={w.id}
    title={w.title}
    bind:position={w.position}
    bind:size={w.size}
    z={w.z}
    persist={w.persist}
    config={w.chatConfig}
    bind:messages={w.messages}
    chatType={w.chatType}
    onFocus={onFocus}
    onRequestClose={onRequestClose}
/>

