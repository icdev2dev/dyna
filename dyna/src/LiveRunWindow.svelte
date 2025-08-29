<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    import { onMount, onDestroy } from 'svelte'; 

    import { io } from 'socket.io-client'; 

    let { 
        id, 
        title = 'Last Updated', 
        run = { agent_id: '', session_id: '' }, 
        position = $bindable({ x: 100, y: 100 }), 
        size = $bindable({ w: 420, h: 240 }),
        z = 1, 
        persist = 'keep', onFocus: onFocusCb, onRequestClose: onRequestCloseCb 
    } = $props(); 
    

    let lastText = $state('');
    let ts = $state(null);
    let error = $state(null);
    //let lastText = ''; 
    //let ts = null; 
    let socket = null; 
    //let error = null; 
    const runKey = () => `${run?.agent_id ?? ''}::${run?.session_id ?? ''}`; 
    onMount(() => { 
        try { 
            // Adjust URL/origin if your API is on another host/port
            // socket = io(window.location.origin, { transports: ['websocket', 'polling'], withCredentials: false, }); 
          socket = io('http://localhost:5000', { transports: ['websocket', 'polling'], withCredentials: false});

            socket.on('connect', () => { socket.emit('subscribe_run', { run_id: runKey() }); }); 
            socket.on('run_update', (data) => { 
                console.log("IN RUN UPDATE: " + data + data.last_text + " " + data.run_id + runKey())
                if (!data || data.run_id !== runKey()) return; 
                if (data.last_text != null) lastText = data.last_text; 
                ts = data.timestamp ?? Date.now(); 
            }); 
            socket.on('connect_error', (e) => { error = `Socket connect error: ${e?.message || e}`; }); 
            socket.on('error', (e) => { error = `Socket error: ${e?.message || e}`; }); } catch (e) { error = String(e); } 
    }); 
    onDestroy(() => { 
        try { 
            socket?.emit?.('unsubscribe_run', { run_id: runKey() }); socket?.close?.(); 
        } catch {} 
    }); 

    function fmtDate() { 
        if (!ts) return ''; try { return new Date(ts).toLocaleString(); } catch { return String(ts); } 
    } 
    function requestCloseLocal() { onRequestCloseCb?.({ id }); } 
</script>


<WindowFrame
  id={id}
  title={title}
  bind:position
  bind:size
  z={z}
  onFocus={onFocusCb}
  onRequestClose={requestCloseLocal}
>
  {#if error}
    <div class="err">Error: {error}</div>
  {/if}

  <div class="live-run-root">
    <div class="last-updated">
      <strong>Last updated:</strong> {fmtDate()}
    </div>
    <pre class="mono box">{lastText ?? ''}</pre>
  </div>
</WindowFrame>

<style>
  .live-run-root { display: grid; grid-template-rows: auto 1fr; height: 100%; gap: 8px; }
  .last-updated { font-size: 0.9rem; color: #374151; }
  .mono.box {
    white-space: pre-wrap;
    word-break: break-word;
    padding: 10px;
    border-radius: 8px;
    background: #0b1020;
    color: #d1e7ff;
    min-height: 120px;
  }
  .err { color: #b91c1c; }
</style>
