
<script>
        
        let {
            messages = $bindable([]),
            config = $bindable({}),
            adapter = undefined,
            chatType = 'default'
        } = $props();

        let input = $state(''); 
        let sending = $state(false); 
        // drive UI 
        let canStop = $state(false); 
        // non-reactive internal handle 
        let abortCtrl; // AbortController | undefined 

        function append(role, content, meta = {}) { 
            const msg = { id: crypto.randomUUID?.() ?? String(Date.now()), role, content, ts: Date.now(), meta }; 
            messages = [...messages, msg]; 
            return msg.id; 
        } 
        async function send() { 
            const text = input.trim(); 
            if (!text || sending) return; 
            input = ''; 
            append('user', text); 
            sending = true; 
            abortCtrl = new AbortController(); 
            canStop = true; 
            const asstId = append('assistant', '', { streaming: true }); 
            try { 
                const client = adapter ?? defaultChatAdapter(); 
                for await (const chunk of client.stream({ messages, config, chatType, signal: abortCtrl.signal })) { 
                    const idx = messages.findIndex(m => m.id === asstId); 
                    if (idx >= 0) { 
                        messages[idx] = { ...messages[idx], content: (messages[idx].content ?? '') + chunk }; 
                        messages = [...messages]; 
                    } 
                } 
            } catch (err) { 
                const idx = messages.findIndex(m => m.id === asstId); 
                if (idx >= 0) { 
                    messages[idx] = { 
                        ...messages[idx], meta: { ...messages[idx].meta, error: String(err) } 
                    }; 
                    messages = [...messages]; 
                } 
            } 
            finally { 
                const idx = messages.findIndex(m => m.id === asstId); 
                if (idx >= 0) { 
                    messages[idx] = { ...messages[idx], meta: { ...messages[idx].meta, streaming: false } }; 
                    messages = [...messages]; 
                } 
                canStop = false; 
                abortCtrl = undefined; 
                sending = false; 
            } 
        } 
        function stop() { 
            abortCtrl?.abort(); 
            canStop = false; 
            abortCtrl = undefined; 
        } 

  // Example adapter: calls your server /api/chat for SSE/streaming
  function defaultChatAdapter() {
    return {
      async *stream({ messages, config, signal }) {
        const res = await fetch('http://localhost:5000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages, config }),
          signal
        });
        const reader = res.body.getReader();
        const td = new TextDecoder();
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const text = td.decode(value, { stream: true });
          // Assume server sends raw text chunks; adapt if using SSE/JSON
          yield text;
        }
      }
    };
  }

  function onKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }
</script>

<div class="chat">
  <div class="messages" data-scroller>
    {#each messages as m (m.id)}
      <div class="msg {m.role}">
        <div class="bubble">
          {m.content}
          {#if m.meta?.error}
            <div class="err">Error: {m.meta.error}</div>
          {/if}
        </div>
      </div>
    {/each}
    {#if sending}
      <div class="msg assistant"><div class="bubble typing">…</div></div>
    {/if}
  </div>


    <div class="composer"> 
        <textarea placeholder="Type a message…" bind:value={input} rows="1" onkeydown={onKey} disabled={sending && canStop}  > </textarea> 
        {#if sending && canStop} 
            <button type="button" onclick={stop}>Stop</button> 
        {:else} <button type="button" onclick={send} disabled={!input.trim() || sending}>Send</button> 
        {/if} 
    </div>

</div>

<style>
  .chat { display: grid; grid-template-rows: 1fr auto; height: 100%; }
  .messages { overflow: auto; padding: 8px; background: #c8a0a0; }
  .msg { display: flex; margin: 6px 0; }
  .msg.user { justify-content: flex-end; }
  .bubble { max-width: 70%; padding: 8px 10px; border-radius: 12px; background: #038e13; }
  .msg.user .bubble { background: #2563eb; color: #fff; }
  .typing { opacity: 0.6; }
  .err { margin-top: 6px; color: #b91c1c; font-size: 0.85em; }
  .composer { display: flex; gap: 8px; padding: 8px; border-top: 1px solid #e2e8f0; background: #fafafa; }
  textarea { flex: 1; resize: none; border: 1px solid #eef0f3; border-radius: 10px; padding: 10px 12px; outline: none; }
  textarea:focus { border-color: var(--fi-accent, #2563eb); box-shadow: 0 0 0 3px rgba(37,99,235,0.20); }
</style>
