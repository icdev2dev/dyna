<!-- GroupField.svelte -->
<script>
  import FormInterpreter from './FormInterpreter.svelte';
  export let label = "";
  export let fields = [];
  export let values = {};
  export let onChange = () => {};
</script>

<fieldset>
  <legend>{label}</legend>
  {#each fields as field}
    <FormInterpreter
      node={field}
      values={values}
      
    />
  {/each}
</fieldset>
