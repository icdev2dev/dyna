<script>
  import TaskGraphWindow from '../TaskGraphWindow.svelte';
  let {
    w,
    onFocus,
    onRequestClose,
    position = $bindable(w.position),
    size = $bindable(w.size),
    z = $bindable(w.z),
    persist = $bindable(w.persist)
  } = $props();
</script>

<TaskGraphWindow
  id={w.id}
  title={w.title}
  bind:position
  bind:size
  bind:z
  onFocus={onFocus}
  onRequestClose={onRequestClose}
  initialPrompt={w.initialPrompt}
  autoGenerate={w.autoGenerate}
/>
