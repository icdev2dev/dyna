<script> 
    import AttributesTable from './Attributes.svelte'; 
    let { 
        value = $bindable({ entities: [] }), 
        disabled = false, 
        readOnly = false, 
        debug = false, 
        onSubmit: onSubmitCb 
    } = $props(); 
    let selectedIndex = $state(0); 
    function ents() { 
        return value.entities ?? (value.entities = []); 
    } 
    let current = $derived(ents()[selectedIndex]); 
    function addEntity() { 
        const next = [...ents(), { schema_name: 'new_schema', attributes: [] }]; 
        value = { ...value, entities: next }; selectedIndex = next.length - 1; 
    } 
    function duplicateEntity(i) { 
        const src = ents()[i]; 
        if (!src) return; 
        const copy = JSON.parse(JSON.stringify(src)); 
        copy.schema_name = `${src.schema_name}_copy`; 
        const next = [...ents(), copy]; 
        value = { ...value, entities: next }; 
        selectedIndex = next.length - 1; 
    } 
    function deleteEntity(i) { 
        if (!window.confirm('Delete this entity?')) return; 
        const next = ents().filter((_, idx) => idx !== i); 
        value = { ...value, entities: next.length ? next : [{ schema_name: 'new_schema', attributes: [] }] }; 
        selectedIndex = 0; 
    } 
    function submit() { onSubmitCb?.({ value }); } 
</script> 

<div class="root"> 
    <aside class="sidebar"> 
        <div class="side-header"> 
            <h2>Schemas</h2> 
            <button class="primary" type="button" onclick={addEntity} disabled={disabled || readOnly}>+ Add</button> 
        </div>
<ul class="entity-list">
  {#each ents() as e, i (i)}
    <li class:selected={i === selectedIndex} onclick={() => (selectedIndex = i)}>
      <div class="name">{e.schema_name || '(unnamed)'}</div>
      <div class="count">{e.attributes?.length || 0} attrs</div>
      <div class="row-actions" onclick={(e) => e.stopPropagation()}>
        <button  title="Duplicate" onclick={() => duplicateEntity(i)} disabled={disabled || readOnly}>⧉</button>
        <button title="Delete" onclick={() => deleteEntity(i)} disabled={disabled || readOnly}>✕</button>
      </div>
    </li>
  {/each}
</ul>

<div class="side-footer">
  <button onclick={submit} disabled={disabled}>Save</button>
</div>
</aside> <main class="editor"> {#if current} <div class="entity-header"> <div class="field"> <label>Schema Name</label> <input type="text" bind:value={current.schema_name} oninput={() => (value = { ...value })} placeholder="e.g., order" disabled={disabled} readonly={readOnly} /> </div> </div>
  <AttributesTable bind:rows={current.attributes} {disabled} {readOnly} />
{/if}

{#if debug}
  <pre class="debug">{JSON.stringify(value, null, 2)}</pre>
{/if}
</main> 
</div> 
<style> 
/* Theme hooks (inherits --fi-accent from WindowFrame) */ 
    :root { 
        --mi-bg: #ffffff; --mi-border: #e5e7eb; --mi-subtle: #f8fafc; --mi-muted: #6b7280; --mi-text: #111827; --mi-accent: var(--fi-accent, #2563eb); 
        --mi-accent-weak: rgba(37, 99, 235, 0.12); --mi-radius: 10px; 
    } 
     
    .root { 
        display: grid; 
        grid-template-columns: 280px 1fr; 
        height: 100%; 
        color: var(--mi-text); background: var(--mi-bg); 
    } 
    
    /* Sidebar */ 
    .sidebar { 
        display: flex; 
        flex-direction: column; 
        border-right: 1px solid var(--mi-border); 
        background: #fff; min-width: 240px; 
    } 
    .side-header { 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        gap: 8px; 
        padding: 12px; 
        border-bottom: 1px solid var(--mi-border); 
    } 
    .side-header h2 { 
        margin: 0; 
        font-size: 0.95rem; 
        font-weight: 700; 
        color: #0f172a; 
    } 
    .entity-list { 
        list-style: none; 
        margin: 0; 
        padding: 0; 
        overflow: auto; 
        flex: 1; 
        background: #fff; 
    } 
    .entity-list li { 
        display: grid; 
        grid-template-columns: 1fr auto auto; 
        gap: 8px; 
        padding: 10px 12px; 
        align-items: center; 
        border-bottom: 1px solid #f3f4f6; 
        background: #fff; 
        cursor: pointer; 
        border-left: 3px solid transparent; 
        transition: background 120ms ease, border-color 120ms ease; 
    } 
    .entity-list li:hover { 
        background: var(--mi-subtle); 
    } 
    .entity-list li.selected { 
        background: #eff6ff; 
        border-left-color: var(--mi-accent); 
    } 
    .entity-list .name { 
        font-weight: 600; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        white-space: nowrap; 
    } .entity-list 
    .count { 
        font-size: 12px; 
        color: var(--mi-muted); 
    } 
    .entity-list .row-actions { display: flex; gap: 6px; } 
    .entity-list .row-actions button { 
        padding: 6px 8px; 
        line-height: 1; 
        border-radius: 8px; 
        border: 1px solid var(--mi-border); background: #fff; 
        color: #334155; 
        cursor: pointer; 
        transition: background 120ms ease, border-color 120ms ease, transform 80ms ease; 
    } 
    .entity-list .row-actions button:hover { 
        background: var(--mi-subtle); border-color: #d1d5db; 
    } 
    .entity-list .row-actions button:active { 
        transform: translateY(1px); 
    } 
    .entity-list .row-actions button:disabled { 
        opacity: 0.6; cursor: not-allowed; 
    } 
    .side-footer { 
        padding: 12px; 
        border-top: 1px solid var(--mi-border); background: #fff; 
    } 
    /* Main editor */ 
    .editor { 
        background: #fff; 
        padding: 14px; 
        overflow: auto; 
    } 
    .entity-header { 
        display: grid; 
        gap: 10px; 
        margin: 4px 0 12px; 
    } 
    label { 
        display: block; 
        font-size: 12px; 
        color: var(--mi-muted); 
        margin-bottom: 6px; 
    } 
    input[type="text"] { 
        width: 100%; 
        padding: 10px 12px; 
        border: 1px solid #d1d5db; 
        border-radius: var(--mi-radius); 
        background: #fff; 
        color: var(--mi-text); 
        outline: none; 
        transition: border-color 120ms, box-shadow 120ms, background-color 120ms; 
    } 
    input[type="text"]::placeholder { 
        color: #9ca3af; 
    } 
    input[type="text"]:focus { 
        border-color: var(--mi-accent); 
        box-shadow: 0 0 0 3px var(--mi-accent-weak); 
    } 
    input[readonly] { 
        background: #f9fafb; 
    } 
    /* Buttons (shared) */ 
    button { 
        padding: 8px 10px; 
        border-radius: 8px; 
        border: 1px solid #d1d5db; 
        background: #fff; 
        color: #111827; 
        cursor: pointer; 
        transition: background 120ms ease, border-color 120ms ease, transform 80ms ease, box-shadow 120ms ease; 
    } 
    button:hover { 
        background: #f8fafc; 
        border-color: #cfd6dd; 
    } 
    button:active { 
        transform: translateY(1px); 
    } 
    button:disabled { 
        opacity: 0.6; 
        cursor: not-allowed; 
    } 
    button.primary { 
        border-color: #1d4ed8; 
        background: var(--mi-accent); 
        color: #fff; 
        font-weight: 700; 
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25); 
    } 
    button.primary:hover { filter: brightness(1.05); } 
    /* Debug block */ 
    .debug { 
        margin-top: 12px; 
        background: #0b1020; 
        color: #d1e7ff; 
        padding: 10px; 
        border-radius: 10px; 
        font-size: 12px; 
        overflow: auto; 
    } 
</style>
