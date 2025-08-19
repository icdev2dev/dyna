<script> 
    // Minimal flat schema: 
    // { type: 'text'|'number'|'select'|'checkbox', name: string, label?: string, options?: (string|{label,value})[] } 
    let { 
        value = $bindable({}),  
        schema = [],  
        disabled = false, 
        readOnly = false, 
        debug = false, 

    //    ({ value }) => void 
        onSubmit: onSubmitCb } = $props()



    function toOptions(opts) { 
        if (!opts) return []; 
        if (typeof opts[0] === 'string') 
            return opts.map((s) => ({ value: s, label: s })); 
        return opts; 
    } 

    function setField(name, type, raw) { 
        let v; 
        if (type === 'checkbox') 
            v = !!raw.checked; 
        else if (type === 'number') v = raw.value === '' ? null : Number(raw.value); 
        else v = raw.value; 
        // reassign to trigger binding 
        value = { ...value, [name]: v }; 
    } 

    function handleSubmit(e) { 
        e.preventDefault(); 
        if (typeof onSubmitCb === 'function') onSubmitCb({ value }); 
    } 
</script> 


<form onsubmit={handleSubmit}> 
    {#each schema as field, i (field.name ?? i)} 
        <div class="fi-field"> {#if field.label} <label for={field.name}>{field.label}</label> {/if}
            {#if field.type === 'select'}
                <select
                id={field.name}
                value={value[field.name] ?? ''}
                onchange={(e) => setField(field.name, 'select', e.currentTarget)}
                disabled={disabled}
                >
                <option value="" disabled selected={value[field.name] == null}>Select...</option>
                {#each toOptions(field.options) as opt}
                    <option value={opt.value} selected={String(opt.value) === String(value[field.name])}>
                    {opt.label}
                    </option>
                {/each}
                </select>

            {:else if field.type === 'checkbox'}
                <input
                id={field.name}
                type="checkbox"
                checked={!!value[field.name]}
                onchange={(e) => setField(field.name, 'checkbox', e.currentTarget)}
                disabled={disabled}
                readonly={readOnly}
                />

            {:else}
                <input
                id={field.name}
                type={field.type === 'number' ? 'number' : 'text'}
                value={value[field.name] ?? ''}
                oninput={(e) => setField(field.name, field.type, e.currentTarget)}
                disabled={disabled}
                readonly={readOnly}
                />
            {/if}
        </div>
    {/each}

    <button type="submit" disabled={disabled}>Submit</button>

    {#if debug}
        <pre>{JSON.stringify(value, null, 2)}</pre>
    {/if}

</form> 

<style> 
/* Form layout: stacked, predictable */ 
    form { 
        display: flex; 
        flex-direction: column; 
        gap: 14px; 
        align-content: start; 
        text-align: left; 
    } 
    .fi-field { 
        display: flex; 
        flex-direction: column; 
        gap: 6px; 
    } 
    /* Strong, left-aligned labels */ 
    .fi-field label { 
        font-weight: 700; 
        font-size: 0.9rem; 
        color: #334155; 
        /* slate-700 */ 
        letter-spacing: 0.01em; 
    } 
    /* Inputs + selects */ 
    input[type="text"], input[type="number"], select { 
        appearance: none; 
        width: 100%; 
        padding: 10px 12px; 
        border: 1px solid #d1d5db; 
        border-radius: 10px; 
        background: #fff; 
        color: #111827; 
        outline: none; 
        transition: border-color 120ms, box-shadow 120ms, background-color 120ms; 
        box-shadow: inset 0 1px 0 rgba(0,0,0,0.02); 
    } 
    input::placeholder { 
        color: #9ca3af; 
    } 
    input:focus, select:focus { 
        border-color: var(--fi-accent, #2563eb); 
        box-shadow: 0 0 0 3px rgba(37,99,235,0.20), inset 0 1px 0 rgba(255,255,255,0.4); 
    } 
    /* Select caret */ 
    select { 
        background-image: linear-gradient(45deg, transparent 50%, #6b7280 50%), linear-gradient(135deg, #6b7280 50%, transparent 50%); 
        background-position: calc(100% - 18px) 50%, calc(100% - 13px) 50%; 
        background-size: 6px 6px, 6px 6px; 
        background-repeat: no-repeat; 
        padding-right: 32px; 
    } 
    /* Checkbox row */ 
    .fi-field:has(input[type="checkbox"]) { 
        flex-direction: row; 
        align-items: center; 
        gap: 10px; 
    } 
    .fi-field:has(input[type="checkbox"]) input[type="checkbox"] { 
        width: 16px; 
        height: 16px; 
        accent-color: var(--fi-accent, #2563eb); 
    } 
    .fi-field:has(input[type="checkbox"]) label { 
        margin: 0; 
        user-select: none; 
        font-weight: 600; 
    } 
    /* Submit button (left aligned) */ 
    form > button[type="submit"] { 
        align-self: flex-start; 
        margin-top: 4px; 
        padding: 10px 14px; 
        border-radius: 10px; 
        border: 1px solid #1d4ed8; background: #2563eb; 
        color: #fff; 
        font-weight: 700; 
        cursor: pointer; 
        transition: filter 120ms ease, transform 80ms ease, box-shadow 120ms ease; box-shadow: 0 2px 8px rgba(37,99,235,0.25); 
        } 
    form > button[type="submit"]:hover { 
        filter: brightness(1.05); 
    } form > 
    button[type="submit"]:active { 
        transform: translateY(1px); 
    } 
    form > button[type="submit"]:disabled { 
        opacity: 0.6; cursor: not-allowed; box-shadow: none; 
    } 
    </style>
