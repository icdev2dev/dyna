<script>
import AgentsListWindow from '../AgentsListWindow.svelte';
let {
    w,
    onFocus,
    onRequestClose,
    // ADD the bindable props you want to relay:
    position = $bindable(w.position),
    size = $bindable(w.size),
    z = $bindable(w.z),
    persist = $bindable(w.persist)
} = $props();
</script>

<AgentsListWindow
  id={w.id}
  title={w.title}
  bind:position
  bind:size
  bind:z
  onFocus={onFocus}
  onRequestClose={onRequestClose}
/>
