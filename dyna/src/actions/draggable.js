export function draggable(node, options = {}) {
    let opts = {
    // get current pos { x, y }
    get: () => ({ x: 0, y: 0 }),
    // set new pos
    set: (_pos) => {},
    // optional: () => ({ w, h }) of the container (canvas/windows layer)
    bounds: undefined,
    // optional: () => ({ w, h }) of the window; if omitted, uses node.offsetWidth/Height
    getSize: undefined,
    ...options
    };

    let active = false;
    let startPointer = { x: 0, y: 0 };
    let startPos = { x: 0, y: 0 };
    let raf = 0;

    function isInteractiveTarget(el) {
        return el.closest?.('button, a, input, textarea, select, label, [role="button"], [contenteditable], [data-nodrag]');
    }

    function onPointerDown(e) {
        if (e.button !== 0) return;
        if (isInteractiveTarget(e.target)) return; // don’t start drag from close button, etc.
        e.preventDefault();
        active = true;
        startPointer = { x: e.clientX, y: e.clientY };
        startPos = opts.get();
        node.setPointerCapture?.(e.pointerId);
        window.addEventListener('pointermove', onPointerMove);
        window.addEventListener('pointerup', onPointerUp);
    }

    function onPointerMove(e) {
        if (!active) return;
        const dx = e.clientX - startPointer.x;
        const dy = e.clientY - startPointer.y;
        let x = startPos.x + dx;
        let y = startPos.y + dy;

        const b = opts.bounds?.();
        if (b) {
            const size = opts.getSize?.() ?? { w: node.offsetWidth, h: node.offsetHeight };
            const bw = b.w ?? b.width ?? 0;
            const bh = b.h ?? b.height ?? 0;
            x = Math.min(Math.max(0, x), Math.max(0, bw - size.w));
            y = Math.min(Math.max(0, y), Math.max(0, bh - size.h));
        }

        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => opts.set({ x, y }));
    }

    function onPointerUp(e) {
        active = false;
        try { 
            node.releasePointerCapture?.(e.pointerId); 
        } catch {}
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

