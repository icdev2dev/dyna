<script> 
    import OrderEditorWindow from '../OrderEditorWindow.svelte'; 
    const { w, onFocus, onRequestClose } = $props(); 
</script>
<OrderEditorWindow
id={w.id}
title={w.title}
bind:position={w.position}
bind:size={w.size}
z={w.z}
persist={w.persist ?? 'destroy'}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>
