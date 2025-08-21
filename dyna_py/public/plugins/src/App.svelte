<script> 
    import Canvas from './Canvas.svelte'; 
    let controller = null; 
    


    function clampNum(n, min, max, fallback) {
        const v = Number(n)
        return Number.isFinite(v) ? Math.min(max, Math.max(min, v)) : fallback
    }

    function sanitizeField(f) {
        if (!f || typeof f !== 'object') return null
        const allowed = ['text', 'number', 'select', 'checkbox']
        const type = allowed.includes(f.type) ? f.type : 'text'
        const name = String(f.name || '').trim()
        if (!name) return null
        const field = { type, name, label: String(f.label || name) }
        if (type === 'select') {
        let opts = Array.isArray(f.options) ? f.options : []
        opts = opts.map(o => typeof o === 'string' ? ({ value: o, label: o }) : o)
                    .filter(o => o && 'value' in o && 'label' in o)
        field.options = opts
        }
        return field
    }

    function sanitizeSpawnConfig(cfg) {
        if (!cfg || typeof cfg !== 'object') return null
        let kind = ['form', 'metadata', 'chat'].includes(cfg.kind) ? cfg.kind : 'form'
        const out = {
        kind,
        title: String(cfg.title || (kind === 'metadata' ? 'Metadata Editor' : kind === 'chat' ? 'Chat' : 'Form')),
        persist: cfg.persist === 'keep' ? 'keep' : 'destroy',
        size: {
            w: clampNum(cfg.size?.w, 320, 1200, 420),
            h: clampNum(cfg.size?.h, 200, 900, 280)
        },
        position: {
            x: clampNum(cfg.position?.x, 0, 4000, 40),
            y: clampNum(cfg.position?.y, 0, 4000, 40)
        }
        }
        if (kind === 'form') {
        out.schema = (Array.isArray(cfg.schema) ? cfg.schema.map(sanitizeField).filter(Boolean) : [])
        out.value = (cfg.value && typeof cfg.value === 'object') ? cfg.value : {}
        } else if (kind === 'metadata') {
        out.value = (cfg.value && typeof cfg.value === 'object') ? cfg.value : { entities: [] }
        } else if (kind === 'chat') {
        out.messages = Array.isArray(cfg.messages) ? cfg.messages : []
        out.chatConfig = (cfg.chatConfig && typeof cfg.chatConfig === 'object') ? cfg.chatConfig : {}
        }
        return out
    }


    async function promptToSchema(text /*, ctx */) {
        // Note: do not send ctx/controller to the server (least privilege)
        const ac = new AbortController()
        const timeout = setTimeout(() => ac.abort(), 15000) // 15s timeout
        try {
            const res = await fetch('http://127.0.0.1:5000/api/prompt-to-schema', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: text }),
                signal: ac.signal
            })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
        
            const data = await res.json()
            console.log(data)

            const items = Array.isArray(data) ? data : [data]
        
            return items.map(sanitizeSpawnConfig).filter(Boolean)
        } finally {
        clearTimeout(timeout)
        }
    }

    /** 
    async function promptToSchema(text, ctx) { 
        return { 
            title: 'Metadata Editor', persist: 'keep', kind: 'metadata' ,
            value: { entities: [] } 
        }; 
    } 
    */

</script> 



<div class="toolbar"> 
    <button type="button" 
        onclick={() => controller?.spawn({ 
                            kind: 'plugin', 
                            title: 'Plugin: HI Hello', 
                            persist: 'keep', 
                            plugin: { id: 'hello.plugin', version: '1.0.1' }, 
                            props: { who: 'Canvas' }, 
                            size: { w: 420, h: 260 }, 
                            position: { x: 80, y: 80 } 
                        }) 
                        } > Open Hello Plugin </button> </div>

<div class="app"> 
    <div class="toolbar"> 
    </div> 
    <Canvas bind:controller={controller} transitions={true} {promptToSchema}/> 
</div> 



<style> 
    .app { 
        inline-size: 100vw; 
        block-size: 100vh; 
        display: grid; 
        grid-template-rows: auto 1fr; 
        background: #85b5e5; 
    } 
    .toolbar { 
        display: flex; 
        gap: 8px; 
        padding: 8px; 
        align-items: center; 
        border-bottom: 1px solid #e5e7eb; 
        background: #ea5e5e; 
    } 

</style>
