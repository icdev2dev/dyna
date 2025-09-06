<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    let { 
        id, 
        title = 'Agent Configs', 
        position = $bindable({ x: 80, y: 80 }), 
        size = $bindable({ w: 960, h: 600 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    
    const AGENT_TYPES = ['JokeAgent', 'PersonaAgent', 'GoalAgent']; 
    let loading = $state(false); 
    let error = $state(null); 
    // List + search 
    let q = $state(''); 
    let items = $state([]); 
    // [{ agent_id, agent_type, agent_description, agents_metadata? }] 
    let selectedId = $state(null); 
    // Detail form 
    let form = $state({ agent_id: '', agent_type: '', agent_description: '', agents_metadata: '{\n}' }); 
    let savedSnapshot = $state(''); 
    let saveBusy = $state(false); 
    let saveErr = $state(null); 
    let deleteBusy = $state(false); 
    let deleteErr = $state(null);
    
    
    let filtered = $derived(
        !q.trim()
        ? items
        : items.filter((it) => {
        const needle = q.trim().toLowerCase();
        return (
        (it.agent_id || '').toLowerCase().includes(needle) ||
        (it.agent_type || '').toLowerCase().includes(needle) ||
        (it.agent_description || '').toLowerCase().includes(needle)
        );
        })
    );


    const isDirty = $derived(() => JSON.stringify(form ?? {}) !== savedSnapshot); 
    function requestClose() { 
        onRequestCloseCb?.({ id, isDirty, value: null, persist }); 
    } 
    function setFormFromItem(it) { 
        form = { agent_id: it?.agent_id ?? '', agent_type: it?.agent_type ?? '', agent_description: it?.agent_description ?? '', agents_metadata: it?.agents_metadata ?? '{\n}' }; savedSnapshot = JSON.stringify(form ?? {}); 
        saveErr = null; deleteErr = null; 
    } 
    async function refresh() { 
        loading = true; 
        error = null; 
        try { 
            const res = await fetch('http://127.0.0.1:5000/api/list-agent-configs'); 
            if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            const data = await res.json(); 
            items = Array.isArray(data) ? data : []; 
            // Reset selection if missing 
            if (selectedId && !items.some(x => x.agent_id === selectedId)) { selectedId = null; } 
            if (selectedId == null && items.length) { selectedId = items[0].agent_id; } 
            const sel = items.find(x => x.agent_id === selectedId); 
            if (sel) setFormFromItem(sel); 
            else { 
                // keep current form if starting fresh 
                if (!isDirty) { newConfig(); } 
            } 
        } catch (e) { error = e.message || String(e); } finally { loading = false; } 
    } 
    $effect(() => { refresh(); }); 
    function confirmNavAway() { 
        if (!isDirty) return true; 
        return window.confirm('You have unsaved changes. Continue and discard them?'); 
    } 
    function selectRow(it) { if (!confirmNavAway()) return; selectedId = it?.agent_id ?? null; setFormFromItem(it); } 
    function newConfig() { 
        if (!confirmNavAway()) return; 
        selectedId = null; 
        form = { agent_id: '', agent_type: '', agent_description: '', agents_metadata: '{\n}' }; 
        savedSnapshot = JSON.stringify(form ?? {}); saveErr = null; deleteErr = null; 
    } 
    function duplicateSelected() { 
        const base = items.find(x => x.agent_id === selectedId); 
        if (!base) return; 
        if (!confirmNavAway()) return; 
        selectedId = null; 
        form = { agent_id: `${base.agent_id || ''}-copy`, agent_type: base.agent_type || '', agent_description: base.agent_description || '', agents_metadata: base.agents_metadata ?? '{\n}' }; 
        savedSnapshot = JSON.stringify(form ?? {}); 
        // treat as clean draft 
        saveErr = null; 
    } 
    function formatJSON() { 
        try { 
            const txt = (form.agents_metadata ?? '').trim(); 
            const v = txt ? JSON.parse(txt) : {}; 
            // form = { ...form, agents_metadata: JSON.stringify(v, null, 2) }; 
            // no error if just formatting 
        } catch (e) { saveErr = 'Invalid JSON: ' + (e?.message || String(e)); } 
    } 
        
    function validateForm() { 
        const id = (form.agent_id || '').trim(); 
        const type = (form.agent_type || '').trim(); 
        if (!id) return 'Agent ID is required.'; 
        if (!type || !AGENT_TYPES.includes(type)) return 'Agent type is required.'; 
      //  const meta = (form.agents_metadata ?? '').trim(); 
      //  if (meta) { try { JSON.parse(meta); } catch (e) { return 'agents_metadata must be valid JSON.'; } } 
        return null; 
    } 
    async function save() { 
        saveErr = null; 
        const err = validateForm(); 
        alert(err)

        if (err) { saveErr = err; return; } 
        saveBusy = true; 
//        alert("hmmm...")
        try { 
            const body = { 
                agent_id: form.agent_id?.trim(), 
                agent_type: form.agent_type?.trim(), 
                agent_description: form.agent_description ?? '', 
                agents_metadata: form.agents_metadata ?? '' 
            }; 
            const res = await fetch('http://127.0.0.1:5000/api/upsert-agent-config', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify(body) }
            );

            if (!res.ok) throw new Error(`HTTP ${res.status}`); 

            savedSnapshot = JSON.stringify(form ?? {}); 
            alert("heer")
            // Re-sync list and keep (possibly renamed) id selected 
            selectedId = form.agent_id?.trim() || null; await refresh(); 
        } catch (e) { saveErr = e.message || String(e); } finally { saveBusy = false; } 
    } 
    async function remove() { 
        deleteErr = null; 
        if (!form.agent_id) return; 
        if (!window.confirm(`Delete agent config "${form.agent_id}"?`)) return; 
        deleteBusy = true; 
        try { 
            const res = await fetch(`http://127.0.0.1:5000/api/delete-agent-config?agent_id=${encodeURIComponent(form.agent_id)}`, { method: 'DELETE' }); if (!res.ok) throw new Error(`HTTP ${res.status}`); 
            // Remove from local list 
            items = items.filter(x => x.agent_id !== form.agent_id); 
            // Select next or new 
            if (items.length) { selectedId = items[0].agent_id; setFormFromItem(items[0]); } else { newConfig(); } 
        } catch (e) { deleteErr = e.message || String(e); } finally { deleteBusy = false; } 
    } 
</script>
<WindowFrame
    id={id}
    title={title}
    bind:position
    bind:size
    {z}
    onFocus={onFocusCb}
    onRequestClose={requestClose}
>

{#snippet headerActions()}
<div class="hdr-actions">
<button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={save} disabled={saveBusy}>Save</button>
<button class="win-close" type="button" onpointerdown={(e)=>e.stopPropagation()} onclick={requestClose} aria-label="Close">×</button>
</div>
{/snippet}

{#snippet children()}
    <section class="cfg-root">
        {#if loading}
            <div>Loading…</div>
        
        {:else if error}
            <div class="err">Error: {error}</div>
        {:else}
            <div class="split">
                <aside class="list-pane">
                    <div class="list-head">
                        <input type="text" placeholder="Search…" bind:value={q} />
                        <button class="primary" type="button" onclick={newConfig}>+ New</button>
                    </div>

                    <ul class="list">
                        {#each filtered as it (it.agent_id)}
                            <li class:selected={it.agent_id === selectedId} onclick={() => selectRow(it)}>
                            <div class="id">{it.agent_id}</div>
                            <div class="meta">{it.agent_type}</div>
                            <div class="desc">{it.agent_description}</div>
                            </li>
                        {/each}
                        {#if !filtered.length}
                            <li class="empty">No configs.</li>
                        {/if}
                    </ul>
                </aside>
                <main class="detail-pane">
                    {#if saveErr}<div class="alert err">{saveErr}</div>{/if}
                    {#if deleteErr}<div class="alert err">{deleteErr}</div>{/if}

                    <div class="grid">
                        <div class="field">
                            <label>Agent ID</label>
                            <input type="text" bind:value={form.agent_id} placeholder="unique id" />
                        </div>

                        <div class="field">
                            <label>Agent Type</label>
                            <select bind:value={form.agent_type}>
                            <option value="" disabled selected={!form.agent_type}>Select agent type…</option>
                            {#each AGENT_TYPES as t}
                                <option value={t}>{t}</option>
                            {/each}
                            </select>
                        </div>

                        <div class="field span-2">
                            <label>Description</label>
                            <input type="text" bind:value={form.agent_description} placeholder="optional description" />
                        </div>

                        <div class="field span-2">
                            <div class="row">
                                <label>agents_metadata (JSON)</label>
                                <button class="btn" type="button" onclick={formatJSON} title="Format JSON">Format JSON</button>
                            </div>
                            <textarea rows="10" bind:value={form.agents_metadata} class="mono"></textarea>
                        </div>
                    </div>

                    <div class="actions">
                    <button type="button" class="btn" onclick={duplicateSelected} disabled={!selectedId}>Duplicate</button>
                    <button type="button" class="btn danger" onclick={remove} disabled={!form.agent_id || deleteBusy}>Delete</button>
                    <div class="spacer"></div>
                    <button type="button" class="btn primary" onclick={save} disabled={saveBusy}>Save</button>
                    </div>
                </main>

            </div>
        {/if}
    </section>
{/snippet}

</WindowFrame>

<style> 
    .hdr-actions { display:flex; gap:6px; } 
    .cfg-root { height: 100%; display: grid; } 
    .split { display: grid; grid-template-columns: 320px 1fr; height: 100%; gap: 12px; } 
    .list-pane { border-right: 1px solid #e5e7eb; padding-right: 8px; display: grid; grid-template-rows: auto 1fr; } 
    .list-head { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding-bottom: 8px; } 
    .list-head input { padding: 8px 10px; border: 1px solid #d1d5db; border-radius: 10px; } 
    .list { list-style: none; margin: 0; padding: 0; overflow: auto; display: grid; gap: 6px; } 
    .list li { border: 1px solid #e5e7eb; border-radius: 10px; padding: 8px 10px; background: #fff; cursor: pointer; } 
    .list li.selected { border-color: #93b0ff; box-shadow: 0 0 0 2px rgba(37,99,235,0.15); } 
    .list .id { font-weight: 800; color: #0f172a; } 
    .list .meta { font-size: 12px; color: #475569; } 
    .list .desc { font-size: 12px; color: #64748b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; } 
    .list .empty { text-align: center; color: #64748b; border: 1px dashed #cbd5e1; } 
    .detail-pane { display: grid; grid-template-rows: auto 1fr auto; gap: 10px; } 
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; } 
    .field { display: grid; gap: 6px; } 
    .field.span-2 { grid-column: span 2; } 
    label { font-size: 12px; color: #6b7280; } 
    input[type="text"], select, textarea { padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; outline: none; transition: border-color 120ms, box-shadow 120ms; } 
    textarea.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; } 
    input:focus, select:focus, textarea:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.16); } 
    .row { display:flex; align-items:center; justify-content: space-between; gap: 8px; } 
    .actions { display: flex; gap: 8px; align-items: center; } 
    .spacer { flex: 1; } 
    .btn { padding: 8px 12px; border-radius: 10px; border: 1px solid #cbd5e1; background: #2065ed; cursor: pointer; } 
    .btn.primary { border-color: #1d4ed8; background: #2563eb; color: #fff; font-weight: 700; } 
    .btn.danger { color: #991b1b; border-color: #fecaca; background: #fee2e2; } 
    .primary { border: 1px solid #1d4ed8; background: #2563eb; color: #fff; font-weight: 700; border-radius: 10px; padding: 8px 12px; } 
    .alert.err { color: #f8f1f1; background: #db2525; border: 1px solid #fee2e2; padding: 10px 12px; border-radius: 10px; } 
    .err { color: #f0e9e9; background: #f38888;} 
</style>
