<script>
  export let label = "";
  export let name = "";
  export let options = [];
</script>
<label>
  {label}
  <select name={name}>
    {#each options as opt}
      <option value={opt}>{opt}</option>
    {/each}
  </select>
</label>

