<script> 
    import { draggable } from './actions/draggable.js'; 
    import { resizable } from './actions/resizeable.js'; 
    let { 
        id, 
        title = 'Window', 
        position = $bindable({ x: 48, y: 48 }), 
        size = $bindable({ w: 420, h: 280 }), 
        z = 1, 
        minSize = { w: 320, h: 160 }, 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb, children, headerActions 
    } = $props(); 
    let winEl = null; 
    function focusSelf() { 
        onFocusCb?.({ id }); 
    } 
    function requestClose() { 
        onRequestCloseCb?.({ id }); 
    } 
    function layerBounds() { 
        const layer = winEl?.parentElement; 
        return { 
            w: layer?.clientWidth ?? window.innerWidth, 
            h: layer?.clientHeight ?? window.innerHeight 
        }; 
    } 
</script> 

<div 
    class="window" 
    bind:this={winEl} 
    style={
        `transform: translate(${position.x}px, ${position.y}px); width:${size.w}px; height:${size.h}px; z-index:${z};`
    } 
    onfocusin={focusSelf} 
    onpointerdown={focusSelf} > 
    
    <div class="win-header" use:draggable={{ 
        get: () => position, 
        set: (p) => (position = p), 
        bounds: layerBounds, 
        getSize: () => size 
        }} > 
        <div class="win-title">{title}</div> 
        <div class="win-actions"> {#if headerActions} {@render headerActions()} {:else} <button class="win-close" type="button" onpointerdown={(e) => e.stopPropagation()} onclick={requestClose} aria-label="Close" > <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"> <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/> </svg> </button> {/if} 
        </div> 
    </div> 
    <div class="win-body"> {@render children?.()} </div> 
    <div class="win-resize" use:resizable={{ get: () => size, set: (s) => (size = s), min: minSize, bounds: layerBounds, getPos: () => position }} aria-label="Resize corner" > </div>
</div>



<style> 
    .window { 
        --win-bg: #ffffff; 
        --win-border: #e5e7eb; 
        --win-radius: 12px; 
        --win-shadow: 0 10px 25px rgba(0,0,0,0.10), 0 8px 10px rgba(0,0,0,0.06); 
        --win-shadow-active: 0 16px 40px rgba(0,0,0,0.18); 
        --header-bg: linear-gradient(180deg, #3b82f6 0%, #2563eb 100%); 
        --header-border: #1e40af; --header-text: #ffffff; /* Pass theme to children via vars if needed */ 
        --fi-accent: #2563eb; --fi-label: #111827; 
    } 
    .window { 
        position: absolute; 
        background: var(--win-bg); 
        border: 1px solid var(--win-border); 
        border-radius: var(--win-radius); 
        box-shadow: var(--win-shadow); 
        overflow: hidden; display: grid; 
        grid-template-rows: auto 1fr; 
        user-select: none; 
        transition: box-shadow 160ms ease, transform 160ms ease; 
        font: 400 14px/1.4 system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; 
    } 
    
    .window:focus-within, .window:active { 
        box-shadow: var(--win-shadow-active); 
    } 
    .win-header { 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        gap: 8px; 
        padding: 8px 10px; 
        background: var(--header-bg); 
        border-bottom: 1px solid var(--header-border); 
        cursor: grab; 
        touch-action: none; 
        /* prevents scroll on touch while dragging */ 
    } 
    .win-header:active { 
        cursor: grabbing; 
    } 
    .win-title { 
        font-weight: 600; 
        font-size: 0.95rem; 
        color: var(--header-text); 
    } 
    .win-actions { 
        display: flex; gap: 6px; 
    } 
    .win-close { 
        inline-size: 28px; 
        block-size: 28px; 
        display: grid; 
        place-items: center; 
        border: 1px solid rgba(255,255,255,0.35); 
        background: rgba(255,255,255,0.16); 
        color: #fff; 
        border-radius: 8px; 
        cursor: pointer; 
        transition: background 140ms ease, transform 120ms ease, box-shadow 140ms ease; 
    } 
    .win-close:hover { 
        background: rgba(255,255,255,0.26); 
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) inset; 
    } 
    .win-close:active { 
        transform: translateY(1px); 
    } 
    .win-body { 
        padding: 14px; 
        overflow: auto; 
        background: #fff; 
    } 
    .win-resize { 
        position: absolute; 
        right: 6px; 
        bottom: 6px; 
        inline-size: 14px; 
        block-size: 14px; 
        cursor: nwse-resize; 
        touch-action: none; /* better resize on touch */ 
    } 
    .win-resize::after { 
        content: ''; 
        position: absolute; 
        inset: 0; 
        background: linear-gradient(135deg, transparent 40%, #c7ccd1 40% 60%, transparent 60%) right bottom/100% 100% no-repeat; opacity: 0.8; 
    } 
</style>