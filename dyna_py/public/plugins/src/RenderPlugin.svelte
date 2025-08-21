<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import { mount } from 'svelte'; 
    // Svelte 5 mount API 
    let { w, onFocus: onFocusCb, onRequestClose: onRequestCloseCb } = $props(); 
    let Comp = $state(null); 
    let loading = $state(false); 
    let error = $state(null); 
    let mountEl = $state(null); 
    let unmount = null; // destroy function from mount() 
    const FLASK = 'http://127.0.0.1:5000'; 
    async function load() { 
        loading = true; 
        error = null; 
        Comp = null; 
        try { 
            // add a cache-buster while iterating to avoid ESM module cache 
            const url = `${FLASK}/plugins/${w.plugin.id}/${w.plugin.version}/index.js?ts=${Date.now()}`; 
            const mod = await import(url); 
            Comp = mod?.default ?? null; } 
            catch (e) { 
                error = String(e); 
            } 
            finally { loading = false; } 
    } // reload on plugin id/version change 
    $effect(() => { 
        if (w?.plugin?.id && w?.plugin?.version) load(); 
    }); 
    // (re)mount when Comp or mountEl changes, cleanup previous 
    $effect(() => { 
        const C = Comp; 
        const el = mountEl; 
        if (!C || !el) return; // clean previous 
        try { 
            unmount?.(); 
        } catch {} 
        unmount = null; 
        // always pass a plain object 
        const who = typeof w?.props?.who === 'string' ? w.props.who : 'Canvas'; 
        // optional: clear container then mount el.replaceChildren(); 
        const dispose = mount(C, { target: el, props: { who } }); 
        // mount() returns a destroy function; keep it 
        unmount = typeof dispose === 'function' ? dispose : null; 
        // cleanup when C or el changes 
        return () => { try { unmount?.(); } catch {}; unmount = null; }; 
    }); 
    // simple approach for prop changes: remount on w.props change 
    $effect(() => { 
        // trigger remount when who changes 
        void w?.props?.who; 
        // no-op: the effect above (Comp/mountEl) will re-run on any state change if you pull who here 
    }); 
    function requestClose() { 
        onRequestCloseCb?.({ id: w.id, isDirty: false, value: null, persist: w.persist }); 
    } 
</script>

<WindowFrame
    id={w.id}
    title={w.title}
    bind:position={w.position}
    bind:size={w.size}
    z={w.z}
    onFocus={onFocusCb}
    onRequestClose={requestClose}>

    {#snippet children()}
    {#if error}<div class="err">{error}</div>
    {:else if loading}<div>Loading…</div>
    {:else}<div class="plugin-mount" bind:this={mountEl}></div>
    {/if}
    {/snippet}
</WindowFrame>
