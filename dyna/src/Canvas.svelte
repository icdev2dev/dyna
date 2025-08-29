<script> 
    import { WINDOW_RENDERERS } from './windows/registry.js'; 
    const CHAT_TYPES = ['default', 'support', 'analysis']; 
    // Props 
    let { 
        engine = { 
                    place({ windows, config, canvasSize }) { 
                        const offset = 28; 
                        const i = windows.length; 
                        return { 
                            x: 40 + (i * offset) % Math.max(1, (canvasSize?.w ?? 1200) - 480), 
                            y: 40 + (i * offset) % Math.max(1, (canvasSize?.h ?? 800) - 320), 
                            w: config?.size?.w ?? 420, h: config?.size?.h ?? 280 }; 
                    } 
        },

        controller = $bindable(null), 
        initial = [], 
        confirmOnDirtyClose = true, 
        persistDefault = 'destroy',
        transitions = true,
        onPromptCb = null,
        promptToSchema = null,
        promptPlaceholder = 'Describe a form you want to create…' 

        } = $props()


     // Make reassignable state into $state 
     let windows = $state([]); // you do windows = [...windows, ...] 
     let closed = $state(new Map()); 
     // if you mutate, reassign to notify 
     let zCounter = $state(1); // you do ++zCounter let canvasEl; // ref; no $state needed unless you reassign manually 

    let canvasEl; 
    let windowsLayerEl;
    let promptText = $state(''); 
    let working = $state(false);


    // Spawn initial windows if provided 
    $effect(() => { 
        if (Array.isArray(initial) && initial.length) { 
            for (const cfg of initial) spawn(cfg); 
        } 
    }); 

    // Controller API 
    function spawn(config) { 
        // config: { id?, title?, schema, value?, persist?, size?, position? } 
        const id = config.id ?? crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`; 
        const schema = config.schema ?? []; 
        const value = config.value ?? {}; 
        const canvasSize = getCanvasSize(); 
        const placed = engine.place({ windows, config, canvasSize }) ?? {}; 
        const pos = config.position ?? { x: placed.x ?? 40, y: placed.y ?? 40 }; 
        const size = config.size ?? { w: placed.w ?? 420, h: placed.h ?? 280 }; 
        const persist = config.persist ?? persistDefault; 

        if (config.kind === 'chat') {
            const chatType = CHAT_TYPES.includes(config.chatType) ? config.chatType : 'default';
            const win = {
                id,
                kind: 'chat',
                title: config.title ?? 'Chat',
                messages: config.messages ?? [],
                chatConfig: config.chatConfig ?? {},
                position: pos,
                chatType,   
                size,
                z: ++zCounter,
                persist
            };
            windows = [...windows, win];
            return id;
        }

        if (config.kind === 'metadata') {
            const win = {
                id,
                kind: 'metadata',
                title: config.title ?? 'Metadata Editor',
                value: config.value ?? { entities: [] },
                position: pos,
                size,
                z: ++zCounter,
                persist
                };

            windows = [...windows, win];
            return id;
        }

        if (config.kind === 'agentsList') {
            const win = {
                id,
                kind: 'agentsList',
                title: config.title ?? 'Agent List',
                value: config.value ?? { entities: [] },
                position: pos,
                size,
                z: ++zCounter,
                persist
                };

            windows = [...windows, win];
            return id;
        }

        if (config.kind === 'orderEditor') {
            const win = {
                id,
                kind: 'orderEditor',
                title: config.title ?? 'Order Editor',
                value: config.value ?? { entities: [] },
                position: pos,
                size,
                z: ++zCounter,
                persist
                };

            windows = [...windows, win];
            return id;
        }

         if (config.kind === 'agentRuns') { 
            const win = { 
                id, 
                kind: 'agentRuns', 
                title: config.title ?? 'Agent Runs', 
                filters: (config.filters && typeof config.filters === 'object') ? config.filters : { agent_id: '', status: '', q: '' }, 
                position: pos, 
                size, 
                z: ++zCounter, 
                persist 
            }; 
            windows = [...windows, win]; 
            return id; 
        } 



        if (config.kind === 'runDetail') {
            const win = {
                id,
                kind: 'runDetail',
                title: config.title ?? 'Last Updated',
                run: {
                    agent_id: String(config.run?.agent_id || ''),
                    session_id: String(config.run?.session_id || '')
                },
                position: pos,
                size,
                z: ++zCounter,
                persist
            };
            windows = [...windows, win];
            return id;
        }










        // NEW: plugin branch
        if (config.kind === 'plugin') {
            
            const win = {
                id,
                kind: 'plugin',
                title: config.title ?? 'Plug In',
                plugin: { id: String(config.plugin?.id || ''), version: String(config.plugin?.version || '') },
                props: (config.props && typeof config.props === 'object') ? config.props : {},
                position: pos,
                size,
                z: ++zCounter,
                persist
            };
            console.log(win)
            windows = [...windows, win];
            return id
        }


        const win = {
            id,
            kind: 'form',
            title: config.title ?? 'Form',
            schema,
            value,
            position: pos,
            size,
            z: ++zCounter,
            persist
        };
        windows = [...windows, win];
        return id;
    }


    function getCanvasSize() { 
        const el = canvasEl; 
        if (!el) 
            return { w: 1200, h: 800 }; 
        const rect = el.getBoundingClientRect(); 
        return { w: rect.width, h: rect.height }; 
    }

     function focus(id) { 
        const idx = windows.findIndex((w) => w.id === id); 
        if (idx === -1) 
            return; 
        const w = windows[idx]; 
        w.z = ++zCounter; 
        windows = [...windows]; 
    }

     function close(id, { force = false } = {}) { 
        const idx = windows.findIndex((w) => w.id === id); 
        if (idx === -1) return; 
        const w = windows[idx]; 
        // Optional: honor force if you later add confirm logic here 
        if (w.persist === 'keep') { 
            closed.set(id, { 
                schema: w.schema, value: w.value, options: { 
                    title: w.title, 
                    size: w.size, 
                    position: w.position, 
                    persist: w.persist 
                } 
            }); 
        } 
        windows = windows.filter((win) => win.id !== id); 
    } 
     function reopen(id) { 
        if (!closed.has(id)) 
            return; 
        const entry = closed.get(id); 
        closed.delete(id); 
        spawn({ id, schema: entry.schema, value: entry.value, ...entry.options }); 
    } 
    function update(id, partial) { 
        const idx = windows.findIndex((w) => w.id === id); 
        if (idx === -1) 
            return; 
        windows[idx] = { ...windows[idx], ...partial }; 
        windows = [...windows]; 
    } 
    controller = { spawn, close, reopen, focus, update, list: () => windows.map((w) => ({ id: w.id, title: w.title })) }; 
     // Event handlers from FormWindow (callbacks passed as props) 
    function onRequestClose({ id, isDirty, value, persist, confirmOnDirtyClose: confirmFlag }) { 
        const needConfirm = confirmFlag ?? confirmOnDirtyClose; 
        if (needConfirm && isDirty) { 
            const ok = window.confirm('You have unsaved changes. Close anyway?'); 
            if (!ok) return; 
        } 
        if (persist === 'keep') { 
            const w = windows.find((w) => w.id === id); 
            if (w) { 
                closed.set(id, { schema: w.schema, value, options: { title: w.title, size: w.size, position: w.position, persist } }); 
            } 
        } 
        windows = windows.filter((w) => w.id !== id); 
    } 
    function onSubmit({ id, value }) { 
        // Hook for global handling (optional) // Example: console.log('Submit from', id, value); 
    } 
    function onFocus({ id }) { 
        focus(id); 
    } 

    // Prompt bar behavior 
    async function submitPrompt(e) { 
        e?.preventDefault?.(); 
        const text = promptText.trim(); 

        if (!text) return; 
        // Notify external listener first 
        if (typeof onPromptCb === 'function') { 
            try { 
                onPromptCb({ text, controller }); 
            } catch (_) {} } 
        if (typeof promptToSchema === 'function') { 
            working = true; 
            try { 
                const result = await promptToSchema(text, { 
                    canvasSize: getCanvasSize(), windows: [...windows], controller 
                });
                console.log(result) 

                const items = Array.isArray(result) ? result : (result ? [result] : []); 
                for (const cfg of items) {
                    if (!cfg || typeof cfg !== 'object') continue;
                    spawn(cfg); 
                } 
            } catch (err) { console.error('promptToSchema failed:', err); } 
            finally { working = false; promptText = ''; } 
        } 
        else { // No auto-spawn; just clear input 
            promptText = ''; 
        } 
    }







function handleShowAgentRuns(e) { 
    const agent_id = e?.detail?.agent_id; 
    if (!agent_id) return; 
    spawn({ 
        kind: 'agentRuns', 
        title: `Runs – ${agent_id}`, 
        persist: 'keep', 
        size: { w: 900, h: 520 }, 
        filters: { agent_id, status: '', q: '' } 
    }); 
}



function handleShowRunDetail(e) {
const aid = e?.detail?.agent_id;
const sid = e?.detail?.session_id;
if (!aid || !sid) return;
spawn({
kind: 'runDetail',
title: `Last Updated — ${sid}`,
persist: 'keep',
size: { w: 700, h: 480 },
run: { agent_id:aid, session_id:sid }
});
}





$effect(() => {
if (!windowsLayerEl) return;
const hRuns = (ev) => handleShowAgentRuns(ev);
const hDetail = (ev) => handleShowRunDetail(ev);
windowsLayerEl.addEventListener('showAgentRuns', hRuns);
windowsLayerEl.addEventListener('showRunDetail', hDetail);
return () => {
windowsLayerEl.removeEventListener('showAgentRuns', hRuns);
windowsLayerEl.removeEventListener('showRunDetail', hDetail);
};
});




</script> 


<div class="canvas" bind:this={canvasEl}> 
    <div class="windows" bind:this={windowsLayerEl} >
        {#each windows as w (w.id)}
            {@const Renderer = WINDOW_RENDERERS[w.kind]} 
            {#if Renderer} 
                <Renderer 
                    w={w} 
                    onFocus={onFocus} 
                    onRequestClose={onRequestClose} 
                    onSubmit={onSubmit} 
                    transitions={transitions}
                    on:showAgentRuns={handleShowAgentRuns} 
                    /> 
            {:else} 
                <div class="window-unknown" style={`z-index:${w.z}`}> Unknown window kind: {w.kind} </div> 
            {/if}
        {/each}
    </div>
    <form class="promptbar" onsubmit={submitPrompt}>
        <input
            type="text"
            placeholder={promptPlaceholder}
            bind:value={promptText}
            disabled={working}
            aria-label="Describe a form to add to the canvas"
        />
        <button type="submit" disabled={working || !promptText.trim()}>
            {working ? 'Thinking…' : 'Create'}
        </button>
    </form> 
</div> 


<style> 
.canvas { 
    position: relative; 
    inline-size: 100%; 
    block-size: 100%; 
    overflow: hidden; 
    background: var(--canvas-bg, #f4f6f8); 
    /* Reserve space for footer using grid: top layer for windows, bottom for prompt */ 
    display: grid; 
    grid-template-rows: 1fr auto; 
} 
.windows { 
    position: relative; 
    /* Absolute children position within this area */ 
    inline-size: 100%; 
    block-size: 100%; 
    overflow: hidden; 
    /* Keep windows inside */ 
} 
.promptbar { 
    display: flex; 
    gap: 8px; 
    padding: 8px; 
    border-top: 1px solid #e2e8f0; 
    background: #ffffffcc; 
    backdrop-filter: blur(6px); 
} 
.promptbar input[type="text"] { 
    flex: 1; 
    padding: 10px 12px; 
    border: 1px solid #d1d5db; 
    border-radius: 10px; 
    background: #a29f9f; 
    outline: none; 
    transition: border-color 120ms, box-shadow 120ms; 
} 
.promptbar input[type="text"]:focus { 
    border-color: var(--fi-accent, #2563eb); 
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.20); 
} 
.promptbar button { 
    padding: 10px 14px; 
    border-radius: 10px; 
    border: 1px solid #1d4ed8; 
    background: #2563eb; 
    color: #fff; 
    font-weight: 700; 
    cursor: pointer; 
    transition: filter 120ms ease, transform 80ms ease, box-shadow 120ms ease; 
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.25); 
} 
.promptbar button:hover { 
    filter: brightness(1.05); 
} 
.promptbar button:active { 
    transform: translateY(1px); 
} 
.promptbar button:disabled { 
    opacity: 0.6; cursor: not-allowed; box-shadow: none; 
} 
</style>

