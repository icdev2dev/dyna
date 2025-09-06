<script>
  import WindowFrame from './WindowFrame.svelte'; 
  import AgentLaunchModal from './AgentLaunchModal.svelte'; 
  let { 
    id, 
    title = 'Agent Configurations', 
    position = $bindable({ x: 100, y: 100 }), 
    size = $bindable({ w: 600, h: 400 }), 
    z = $bindable(1), 
    persist = 'keep', 
    onFocus: onFocusCb, 
    onRequestClose: onRequestCloseCb 
  } = $props(); 
  let loading = $state(true); 
  let error = $state(null); 
  let agentConfigs = $state([]); 
  let selected = $state({}); 

  let launchAgentType = $state('');

  // Popover 
  let menuOpen = $state(false); 
  let menuX = $state(0), menuY = $state(0); 
  let menuAgent = $state(null); 
  // Launch modal 
  let launchOpen = $state(false); 
  let launchBusy = $state(false); 
  let launchErr = $state(null); 
  let launchAgentId = $state(''); 
  // A DOM node inside the window to dispatch custom events (for Canvas) 
  let rootEl = null; 
  function toggleSelect(agent_id, checked) { 
    selected = { ...selected, [agent_id]: checked }; 
  } 
  function selectAllRows(checked) { 
    selected = Object.fromEntries(agentConfigs.map(a => [a.agent_id, checked])); 
  } 
  function anySelected() { 
    return Object.values(selected).some(Boolean); 
  } 
  function selectedIds() { 
    return Object.entries(selected).filter(([,v]) => v).map(([id]) => id); 
  } 
  function refresh() { 
    loading = true; 
    error = null; 
    (async () => { 
      try { 
        const res = await fetch('http://127.0.0.1:5000/api/list-agent-configs'); 
        if (!res.ok) throw new Error(`Server error: ${res.status}`); 
        agentConfigs = await res.json(); 
        const ids = new Set(agentConfigs.map(a => a.agent_id)); 
        selected = Object.fromEntries(Object.entries(selected).filter(([id]) => ids.has(id))); 
      } catch (e) { error = e.message || String(e); } loading = false; })(); 
  } 
  
  $effect(() => { refresh(); }); 
  
  function requestClose() { 
    onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); 
  } 
  function openMenu(evt, agent) { 
    menuAgent = agent; 
    menuX = evt.clientX; menuY = evt.clientY;
    menuOpen = true; 
  } 
  function closeMenu() { 
    menuOpen = false; 
    menuAgent = null; 
  } 
  function openLaunch(agent) { 
    launchErr = null; 
    launchAgentId = agent?.agent_id ?? ''; 
    launchAgentType = agent?.agent_type ?? ''; // NEW
    launchOpen = true; 
  } 
  function showProps(agent) { 
    alert('Agent Properties:\n' + JSON.stringify(agent, null, 2)); 
  } 
  function deleteSelected() { 
    if (!anySelected()) return; 
    if (!window.confirm(`Delete ${selectedIds().length} selected agent(s)?`)) return; 
    agentConfigs = agentConfigs.filter(cfg => !selected[cfg.agent_id]);
    selected = {}; 
    closeMenu(); 
  } // Handle OK from modal: call API and, on success, close and show runs 
  
  async function handleLaunchConfirm({ agent_id, session_id, prompt, config }) { 
    launchBusy = true; 
    launchErr = null; 





    try {
      if ((launchAgentType || '').toLowerCase() === 'goalagent') {
// Tell Canvas to open TaskGraph with this prompt
      try {
          rootEl?.dispatchEvent(new CustomEvent('openTaskGraph', {
          detail: { prompt: prompt || '' },
          bubbles: true,
          composed: true
          }));
        } catch {}
        launchOpen = false;
        return;
      }
     
      const res = await fetch('http://127.0.0.1:5000/api/create-agent', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ agent_id, session_id, input: prompt, config }) 
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`); 
      launchOpen = false; 
      // Trigger runs window for this agent via a bubbling DOM CustomEvent 
      try { 
        rootEl?.dispatchEvent(new CustomEvent('showAgentRuns', { detail: { agent_id }, bubbles: true, composed: true })); 
      } catch {} 
    } 
    catch (e) { launchErr = e.message || String(e); } 
    finally { launchBusy = false; } }

</script>


<WindowFrame
{id}
{title}
bind:position
bind:size
{z}
onFocus={onFocusCb}
onRequestClose={requestClose} >

{#snippet children()}
  <section bind:this={rootEl} style="padding: 18px;">
    <div class="header-row">
      <span>Agent Configurations</span>
      <div>
        <button
                type="button"
                class="delete-btn"
                disabled={!anySelected()}
                onclick={deleteSelected}
                title="Delete selected agents"
              >
        🗑️ Delete Selected
        </button>
        <button type="button" class="refresh-btn" onclick={refresh} title="Refresh list">⟳ Refresh</button>
      </div>
    </div>
    {#if loading}
      <div>Loading…</div>
    {:else if error}
      <div class="err">{error}</div>
    {:else}
      {#if agentConfigs.length}
        <table class="agent-table">
        <thead>
        <tr>
        
        <th>ID</th>
        <th>Type</th>
        <th>Description</th>
        </tr>
        </thead>
        <tbody>
        {#each agentConfigs as cfg}
        <tr onclick={e => openMenu(e, cfg)} tabindex="0" style="cursor:pointer">
        
        <td>{cfg.agent_id}</td>
        <td>{cfg.agent_type}</td>
        <td>{cfg.agent_description}</td>
        </tr>
        {/each}
        </tbody>
        </table>
      {:else}
        <div>No agent configs found.</div>
      {/if}
    {/if}
  </section>
{/snippet}
</WindowFrame>

{#if menuOpen}
  {@const t = (menuAgent?.agent_type || '').toLowerCase()}
    
  <div 
    class="popover-menu" 
    style={`left: ${menuX}px; top: ${menuY}px;`} 
    onclick={e => e.stopPropagation()} > 
    `
  <button
    class="pmenu-btn"
    onclick={() => {
      // Ask for seed only for GoalAgent (optional)
//      const seed = t === 'goalagent' ? (window.prompt('Describe your goal (optional):', '') || '') : '';
      rootEl?.dispatchEvent(new CustomEvent('openAgentRun', {
        detail: {
        agent_id: menuAgent.agent_id,
        agent_type: menuAgent.agent_type,
        prompt: ''
        },
        bubbles: true, composed: true
      }));
      closeMenu();
    }}>
    {t === 'goalagent' ? '🎯 Open Goal Planner' : '🚀 Launch Agent Run'}
  </button>





      <button 
        class="pmenu-btn" 
        onclick={() => { /* show runs */ rootEl?.dispatchEvent(new CustomEvent('showAgentRuns', { detail: { agent_id: menuAgent.agent_id }, bubbles: true, composed: true })); closeMenu(); }}>📊 
        Show Agent Runs
      </button> 
      <button class="pmenu-btn" onclick={() => { showProps(menuAgent); closeMenu(); }}>ℹ️ 
        More Properties
      </button> 
    </div> 
  <div class="backdrop" onclick={closeMenu}></div> 
{/if}

<AgentLaunchModal
open={launchOpen}
agentId={launchAgentId}
bind:busy={launchBusy}
submitError={launchErr}
onConfirm={handleLaunchConfirm}
onCancel={() => (launchOpen = false)}
/>



<style>
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
  font-weight: bold;
  font-size: 1.1em;
  gap: 12px;
}
.refresh-btn {
  background: #1e90ff;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 1em;
  margin-left: 8px;
}
.refresh-btn:hover { filter: brightness(1.1); }
.delete-btn {
  background: #e04038;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 1em;
}
.delete-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.agent-table { border-collapse: collapse; width: 100%; margin-top: 12px; }
.agent-table th, .agent-table td { border: 1px solid #ccc; padding: 6px 10px; text-align: left; }
.agent-table th { background: #3482d0; color: #fff;}
.agent-table tr { background: #629749; }
.agent-table tr:hover { background: #236a15; }
.agent-table th input[type="checkbox"] { width: 1em; height: 1em; accent-color: #236a15;}
.agent-table td input[type="checkbox"] { width: 1em; height: 1em; accent-color: #3482d0;}

.err { color: #b91c1c; }

.popover-menu {
  position: fixed;
  z-index: 1000;
  background: #938ae7;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 6px 0;
  min-width: 180px;
  font-size: 1em;
}
.pmenu-btn {
  display: block;
  width: 100%;
  text-align: left;
  border: none; background: none; padding: 8px 18px; cursor: pointer;
}
.pmenu-btn:hover { background: #2957b3; }
.backdrop {
  position: fixed; inset: 0;
  background: transparent;
  z-index: 999;
}
</style>