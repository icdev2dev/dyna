<script> import GoalAgentRunWindow from '../GoalAgentRunWindow.svelte'; let { w, onFocus, onRequestClose, position = $bindable(w.position), size = $bindable(w.size), z = $bindable(w.z) } = $props(); </script>
<GoalAgentRunWindow
id={w.id}
title={w.title}
bind:position
bind:size
bind:z
seedPrompt={w.seedPrompt}
onFocus={onFocus}
onRequestClose={onRequestClose}
/>