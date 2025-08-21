<script> 
    let { 
        rows = $bindable([]), 
        disabled = false, 
        readOnly = false, 
        dataTypes = ['string', 'number', 'boolean', 'date', 'relation', 'GUID'], 
        uiControls = ['text', 'textarea', 'number', 'select', 'date', 'checkbox', 'table', 'relation'], 
        relTypes = ['one_to_one', 'one_to_many'] 
    } = $props(); 
    
    function addRow() { 
        const row = { 
            attribute_name: '', 
            data_type: 'string', 
            label: '', 
            required: false, 
            ui_control: 'text', 
            description: '', 
            parent_schema_name: null, 
            related_schema: null, 
            relation_type: null 
        }; 
        rows = [...rows, row]; 
    } 
    function del(i) { 
        rows = rows.filter((_, idx) => idx !== i); 
    } 
    function move(i, dir) { 
        const j = i + dir; 
        if (j < 0 || j >= rows.length) return; 
        const next = [...rows]; [next[i], next[j]] = [next[j], next[i]]; 
        rows = next; 
    } 
</script> 

<div class="attr-table"> 
    <div class="scroller"> 
        <table class="grid" role="grid" aria-label="Attributes"> 
            <colgroup> 
                <col style="width:150px" /> 
                <col style="width:130px" /> 
                <col style="width:150px" /> 
                <col style="width:90px" /> 
                <col style="width:130px" /> 
                <col style="width:200px" /> 
                <col style="width:180px" /> 
                <col style="width:220px" /> 
                <col style="width:160px" /> 
                <col style="width:140px" /> 
            </colgroup> 
            <thead> 
                <tr> 
                    <th>Attribute Name</th> 
                    <th>Data Type</th> 
                    <th>Label</th> 
                    <th>Required</th> 
                    <th>UI Control</th> 
                    <th>Description</th> 
                    <th>Parent Schema</th> 
                    <th>Related Schema</th> 
                    <th>Relation Type</th> 
                    <th></th> 
                </tr> 
            </thead> 
            <tbody> 
                {#each rows as a, idx (idx)} 
                    <tr> 
                        <td>
                            <input type="text" bind:value={a.attribute_name} disabled={disabled} readonly={readOnly} />
                        </td>
                        <td>
                        <select bind:value={a.data_type} disabled={disabled || readOnly}>
                            {#each dataTypes as t}<option value={t}>{t}</option>{/each}
                        </select>
                        </td>

                        <td><input type="text" bind:value={a.label} disabled={disabled} readonly={readOnly} /></td>

                        <td class="center">
                        <input class="chk" type="checkbox" bind:checked={a.required} disabled={disabled || readOnly} />
                        </td>

                        <td>
                            <select bind:value={a.ui_control} disabled={disabled || readOnly}>
                                {#each uiControls as u}<option value={u}>{u}</option>{/each}
                            </select>
                        </td>

                        <td><input type="text" bind:value={a.description} disabled={disabled} readonly={readOnly} /></td>

                        <td><input type="text" bind:value={a.parent_schema_name} placeholder="e.g., order" disabled={disabled} readonly={readOnly} /></td>

                        <td><input type="text" bind:value={a.related_schema} placeholder="e.g., order_line_items" disabled={disabled} readonly={readOnly} /></td>

                        <td>
                            <select bind:value={a.relation_type} disabled={disabled || readOnly}>
                                <option value={null}>—</option>
                                {#each relTypes as r}<option value={r}>{r}</option>{/each}
                            </select>
                        </td>

                        <td class="row-actions">
                        <button type="button" title="Up" onclick={() => move(idx, -1)} disabled={disabled || readOnly || idx === 0}>↑</button>
                        <button type="button" title="Down" onclick={() => move(idx, +1)} disabled={disabled || readOnly || idx === rows.length - 1}>↓</button>
                        <button type="button" title="Delete" onclick={() => del(idx)} disabled={disabled || readOnly}>✕</button>
                        </td>
                    </tr>
                {/each}

                {#if !rows || rows.length === 0}
                <tr><td class="empty" colspan="10">No attributes yet. Click “Add Attribute”.</td></tr>
                {/if}
            </tbody>
        </table>
    </div> 
    <div class="tfoot"> 
        <button type="button" class="primary" onclick={addRow} disabled={disabled || readOnly}>+ Add Attribute</button> 
    </div> 
</div> 

<style> 
    :root { 
        --mi-border: #e5e7eb; 
        --mi-subtle: #f8fafc; 
        --mi-text: #111827; 
        --mi-muted: #6b7280; 
        --mi-accent: var(--fi-accent, #2563eb); 
        --mi-accent-weak: rgba(37, 99, 235, 0.12); 
        --mi-radius: 10px; 
        --table-min-width: 1500px; 
        /* force H-scroll on narrow windows */ 
        --cell-pad-y: 8px; --cell-pad-x: 10px; --control-h: 36px; 
    } 
    .attr-table { 
        display: grid; 
        grid-template-rows: 1fr auto; 
        border: 1px solid var(--mi-border); 
        border-radius: var(--mi-radius); 
        background: #fff; 
        overflow: hidden; 
    } 
    .scroller { 
        overflow: auto; 
        /* both axes */ 
    } 
    table.grid { 
        width: 100%; 
        min-width: var(--table-min-width); 
        border-collapse: separate;
        border-spacing: 0; 
        
    } 
    thead th { 
        position: sticky; 
        top: 0; z-index: 1; 
        text-align: left; 
        background: var(--mi-subtle); 
        color: #374151; 
        font-weight: 700; 
        padding: 10px var(--cell-pad-x); 
        border-bottom: 1px solid var(--mi-border); 
    } 
    tbody td { 
        padding: var(--cell-pad-y) var(--cell-pad-x); 
        border-bottom: 1px solid #f3f4f6; 
        vertical-align: middle; background: #fff; 
    } 
    tbody tr:last-child td { 
        border-bottom: none; 
    } 
    .center { 
        text-align: center; 
    } 
    /* Controls */ 
    input[type="text"], select { 
        width: 100%; 
        height: var(--control-h); 
        padding: 8px 10px; 
        border: 1px solid #d1d5db; 
        border-radius: 8px; 
        background: #fff; 
        color: var(--mi-text); 
        outline: none; 
        transition: border-color 120ms, box-shadow 120ms, background-color 120ms; 
    } 
    input[type="text"]::placeholder { 
        color: #9ca3af; 
    } 
    input[type="text"]:focus, select:focus { 
        border-color: var(--mi-accent); box-shadow: 0 0 0 3px var(--mi-accent-weak); 
    } 
    input[readonly] { 
        background: #f9fafb; 
    } 
    .chk { 
        width: 16px; height: 16px; accent-color: var(--mi-accent); 
    } 
    .row-actions { 
        display: flex; gap: 6px; justify-content: flex-end; 
    } 
    .row-actions button { 
        padding: 6px 8px; 
        border-radius: 8px; 
        border: 1px solid var(--mi-border); 
        background: #fff; color: #334155; cursor: pointer; 
        transition: background 120ms ease, border-color 120ms ease, transform 80ms ease; 
    } 
    .row-actions button:hover { 
        background: var(--mi-subtle); border-color: #d1d5db; 
    } 
    .row-actions button:active { transform: translateY(1px); } 
    .row-actions button:disabled { 
        opacity: 0.6; 
        cursor: not-allowed;
    } 
    .empty { 
        color: var(--mi-muted); 
        padding: 12px; 
        text-align: center; 
    } 
    .tfoot { 
        padding: 10px 12px; border-top: 1px solid var(--mi-border); 
        background: #fff; 
    } 
    .primary { 
        border: 1px solid #1d4ed8; 
        background: var(--mi-accent); 
        color: #fff; 
        font-weight: 700; 
        border-radius: 8px; 
        padding: 8px 12px; 
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25); 
    } 
    .primary:hover { 
        filter: brightness(1.05); 
    } 
</style>
