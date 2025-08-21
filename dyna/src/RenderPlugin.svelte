<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    // Runes props 
    let { w, onFocus: onFocusCb, onRequestClose: onRequestCloseCb } = $props(); 
    // State 
    let loading = $state(false); 
    let error = $state(null); 
    
    // DOM mount target (must be reactive in Runes) 
    let mountEl = $state(null); 
    // Plugin loader + lifecycle 
    let mountPluginFn = $state(null); 
    // function (el, props) => () => void 
    let unmount = null; 
    // Cache-buster for dev; in prod rely on versioned URL 
    const nowTs = () => Date.now(); 
    // Helper: plugin URL (defaults to Flask on 5000; allow override via w.plugin.base) 
    function pluginUrl() { const base = w?.plugin?.base || 'http://127.0.0.1:5000'; const ts = w?.plugin?.ts || nowTs(); return `${base}/plugins/${w.plugin.id}/${w.plugin.version}/index.js?ts=${ts}`; } 
    // Load module, pick mountPlugin 
    async function load() { 
        loading = true; 
        error = null; 
        mountPluginFn = null; 
        try { 
            const url = pluginUrl(); 
            const mod = await import(url); 
            if (typeof mod.mountPlugin !== 'function') { 
                throw new Error('mountPlugin export not found in plugin module'); 
            } 
            mountPluginFn = mod.mountPlugin; 
        } catch (e) { error = String(e); } finally { loading = false; } 
    } 
    // Load when plugin id/version/base changes 
    $effect(() => { 
        // Touch dependencies so the effect re-runs on change 
        void w?.plugin?.id; void w?.plugin?.version; void w?.plugin?.base; load(); 
    }); 
    // Stable, plain props for the plugin (avoid passing proxies) 
    const propsKey = $derived(JSON.stringify(w?.props ?? {})); 
    function makePlainProps() { 
        const p = w?.props; 
        return p && typeof p === 'object' && !Array.isArray(p) ? { ...p } : {}; 
    } 
    // Mount/remount when loader ready, mountEl available, or props change 
    $effect(() => { 
        const mp = mountPluginFn; 
        const el = mountEl; 
        const _pk = propsKey; // dependency to trigger on props change 
        if (!mp || !el) return; try { unmount?.(); } 
        catch {} unmount = null; 
        const props = makePlainProps(); 
        try { 
            unmount = mp(el, props); 
            // plugin’s own runtime mounts and returns destroy 
        } catch (e) { error = `Plugin mount failed: ${e}`; unmount = null; } 
        // Cleanup when mp/el/props change or component unmounts 
        return () => { try { unmount?.(); } catch {}; unmount = null; }; }); 
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
    onRequestClose={requestClose} >

{#snippet children()}
    {#if error}<div class="err">{error}</div>
    {:else if loading}<div>Loading…</div>
    {:else}<div class="plugin-mount" bind:this={mountEl}></div>
    {/if}
{/snippet}
</WindowFrame>
