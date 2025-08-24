<script>
import WindowFrame from './WindowFrame.svelte';

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

// Checkbox state: agent_id -> true/false
let selected = $state({});

// Popover menu state
let menuOpen = $state(false);
let menuX = $state(0), menuY = $state(0);
let menuAgent = $state(null);

// Handle selection
function toggleSelect(agent_id, checked) {
  selected = { ...selected, [agent_id]: checked };
}
function selectAllRows(checked) {
  selected = {};
  for (const c of agentConfigs) selected[c.agent_id] = checked;
}
function anySelected() {
  return Object.values(selected).some(v => v);
}
function selectedIds() {
  return Object.entries(selected).filter(([,v]) => v).map(([id]) => id);
}

// Refresh/fetch
function refresh() {
  loading = true; error = null;
  (async () => {
    try {
      const res = await fetch('http://127.0.0.1:5000/api/list-agent-configs');
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      agentConfigs = await res.json();
      // Prune selected map after reload
      const ids = new Set(agentConfigs.map(a => a.agent_id));
      selected = Object.fromEntries(Object.entries(selected).filter(([id]) => ids.has(id)));
    } catch (e) {
      error = e.message || String(e);
    }
    loading = false;
  })();
}

$effect(() => { refresh(); });

function requestClose() { onRequestCloseCb?.({ id, isDirty: false, value: null, persist }); }

function openMenu(evt, agent) {
  menuAgent = agent;
  menuX = evt.clientX; menuY = evt.clientY; menuOpen = true;
}
function closeMenu() { menuOpen = false; menuAgent = null; }

function launchAgent(agent) {
  alert('Would launch agent: ' + agent.agent_id);
}
function showProps(agent) {
  alert('Agent Properties:\n' + JSON.stringify(agent, null, 2));
}

// Delete selected (demo: just filters client-side, or implement API call if needed)
function deleteSelected() {
  if (!anySelected()) return;
  if (!window.confirm(`Delete ${selectedIds().length} selected agent(s)?`)) return;
  // Actual deletion: could call backend API here!
  agentConfigs = agentConfigs.filter(cfg => !selected[cfg.agent_id]);
  // Remove from selection as well
  selected = {};
  closeMenu();
}
</script>

<WindowFrame
  {id}
  {title}
  bind:position
  bind:size
  {z}
  onFocus={onFocusCb}
  onRequestClose={requestClose}
>
  {#snippet children()}
    <section style="padding: 18px;">
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
                <th>
                  <input
                    type="checkbox"
                    checked={agentConfigs.length && selectedIds().length === agentConfigs.length}
                    indeterminate={selectedIds().length > 0 && selectedIds().length < agentConfigs.length}
                    onclick={e => selectAllRows(e.target.checked)}
                    aria-label="Select all"
                  />
                </th>
                <th>ID</th>
                <th>Type</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {#each agentConfigs as cfg}
                <tr
                  onclick={e => openMenu(e, cfg)}
                  tabindex="0"
                  style="cursor:pointer"
                >
                  <td onclick={e => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={!!selected[cfg.agent_id]}
                      onclick={e => toggleSelect(cfg.agent_id, e.target.checked)}
                      aria-label="Select agent"
                    />
                  </td>
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
  <div
    class="popover-menu"
    style={`left: ${menuX}px; top: ${menuY}px;`}
    onclick={e => e.stopPropagation()}
  >
    <button class="pmenu-btn" onclick={() => { launchAgent(menuAgent); closeMenu(); }}>🚀 Launch Agent</button>
    <button class="pmenu-btn" onclick={() => { showProps(menuAgent); closeMenu(); }}>ℹ️ More Properties</button>
    <button class="pmenu-btn" onclick={closeMenu}>Cancel</button>
  </div>
  <div class="backdrop" onclick={closeMenu}></div>
{/if}

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