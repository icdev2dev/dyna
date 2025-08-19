export function resizable(node, options = {}) {
    let opts = {
    // get current size { w, h }
    get: () => ({ w: 0, h: 0 }),
    // set new size
    set: (_size) => {},
    // optional: min size
    min: { w: 160, h: 120 },
    // optional: () => ({ w, h }) of the container
    bounds: undefined,
    // optional: current position { x, y } to clamp size to container
    getPos: undefined,
    ...options
    };

    let active = false;
    let startPointer = { x: 0, y: 0 };
    let startSize = { w: 0, h: 0 };
    let raf = 0;

    function onPointerDown(e) {
        if (e.button !== 0) return;
        e.preventDefault();
        active = true;
        startPointer = { x: e.clientX, y: e.clientY };
        startSize = opts.get();
        node.setPointerCapture?.(e.pointerId);
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
    }

    function onPointerMove(e) {
        if (!active) return;
        const dx = e.clientX - startPointer.x;
        const dy = e.clientY - startPointer.y;
        let w = Math.max(opts.min.w, startSize.w + dx);
        let h = Math.max(opts.min.h, startSize.h + dy);

        const b = opts.bounds?.();
        const pos = opts.getPos?.();
        if (b && pos) {
            const bw = b.w ?? b.width ?? 0;
            const bh = b.h ?? b.height ?? 0;
            const maxW = Math.max(0, bw - pos.x);
            const maxH = Math.max(0, bh - pos.y);
            w = Math.min(w, maxW);
            h = Math.min(h, maxH);
        }

        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => opts.set({ w, h }));
    }

    function onPointerUp(e) {
        active = false;
        try { node.releasePointerCapture?.(e.pointerId); } catch {}
        window.removeEventListener('pointermove', onPointerMove);
        window.removeEventListener('pointerup', onPointerUp);
        cancelAnimationFrame(raf);
    }

    node.addEventListener('pointerdown', onPointerDown);

    return {
        update(newOptions = {}) { opts = { ...opts, ...newOptions }; },
        destroy() {
            node.removeEventListener('pointerdown', onPointerDown);
            window.removeEventListener('pointermove', onPointerMove);
            window.removeEventListener('pointerup', onPointerUp);
            cancelAnimationFrame(raf);
        }
    };
}