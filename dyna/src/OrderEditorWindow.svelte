<script> 
    import WindowFrame from './WindowFrame.svelte'; 
    const sampleVendors = ['Adobe', 'Microsoft', 'Amazon', 'Apple', 'Oracle']; 
    const sampleProducts = ['3 year commit', 'Acrobat', 'Photoshop', 'Office 365', 'AWS Credits']; 
    let { 
        id, 
        title = 'Order & Rules Editor', 
        position = $bindable({ x: 80, y: 80 }), 
        size = $bindable({ w: 960, h: 600 }), 
        z = $bindable(1), 
        persist = 'keep', 
        onFocus: onFocusCb, 
        onRequestClose: onRequestCloseCb 
    } = $props(); 
    
    // Order state 
    let order = $state({ vendor: '', products: [], lineItems: [] }); 
    // Product chips autocomplete 
    let productInput = $state(''); 
    let productDropdown = $derived( productInput ? sampleProducts.filter(p => p.toLowerCase().includes(productInput.toLowerCase()) && !order.products.includes(p)) : sampleProducts.filter(p => !order.products.includes(p)) ); 
    // Line items 
    function addLineItem() { order.lineItems = [...order.lineItems, { product: '', quantity: 1, price: 0 }]; } 
    function removeLineItem(idx) { order.lineItems = order.lineItems.filter((_, i) => i !== idx); } 
    function updateLineItem(idx, key, value) { order.lineItems[idx][key] = value; order = { ...order }; } 
    function lineItemTotal(item) { return (Number(item.quantity) || 0) * (Number(item.price) || 0); } 
    function orderTotal() { return order.lineItems.reduce((s, i) => s + lineItemTotal(i), 0); } 
    // Products multiselect 
    function addProductChip(p) { if (!order.products.includes(p)) { order.products = [...order.products, p]; productInput = ''; } } 
    function removeProductChip(p) { order.products = order.products.filter(prod => prod !== p); } 
    // Rules state 
    let rules = $state([]); 
    let newRuleInput = $state(''); 
    // Rules actions 
    function addRule() { const val = newRuleInput.trim(); if (!val) return; rules = [ ...rules, { description: val, user: 'milind', created: new Date().toLocaleDateString(), expanded: false, stub: null } ]; newRuleInput = ''; } 
    function removeRule(idx) { rules = rules.filter((_, i) => i !== idx); } 
    function toggleRuleExpand(idx) { rules[idx].expanded = !rules[idx].expanded; rules = [...rules]; } 
    function moveRule(idx, dir) { const j = idx + dir; if (j < 0 || j >= rules.length) return; const next = [...rules]; [next[idx], next[j]] = [next[j], next[idx]]; rules = next; } 
    // Check rules (stub) 
    function checkRules() { rules = rules.map(rule => { if (/adobe.*3 year commit/i.test(rule.description)) { if ( order.vendor?.toLowerCase() === 'adobe' && order.products?.map((p) => p.toLowerCase()).includes('3 year commit') ) { if (orderTotal() < 1000) return { ...rule, stub: 'fail' }; return { ...rule, stub: 'pass' }; } return { ...rule, stub: null }; } return { ...rule, stub: null }; }); } 
</script>


<WindowFrame
{id}
{title}
bind:position
bind:size
{z}
onFocus={onFocusCb}
onRequestClose={() => onRequestCloseCb?.({ id, isDirty: false, value: order, persist })}
>
{#snippet children()}
<main class="order-editor-root">
<!-- LEFT: Order -->
<section class="order-section">
<div class="form-header">Edit Order</div>

    <div class="form-grid">
      <div class="form-group">
        <label for="vendor">Vendor</label>


        <input list="vendors" id="vendor" placeholder="Select vendor" bind:value={order.vendor} class="input-lg" />
        
        <datalist id="vendors">
          {#each sampleVendors as v}
            <option value={v}></option>
          {/each}
        </datalist>
      </div>

      <div class="form-group span-2">
        <label>Products</label>
        <div class="prod-chips">
          {#each order.products as p}
            <div class="chip">
              {p}
              <button type="button" class="chip-del" onclick={() => removeProductChip(p)} aria-label="Remove">&times;</button>
            </div>
          {/each}

          <input type="text" placeholder="Add product" bind:value={productInput} onkeydown={e => { if (e.key === 'Enter' && productInput.trim()) addProductChip(productInput.trim()); }} class="chip-input" />

          
          {#if productDropdown.length && productInput}
            <div class="prod-dropdown">
              {#each productDropdown as prod}
                <div class="prod-opt" onclick={() => addProductChip(prod)}>{prod}</div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>

    <div class="form-header" style="margin-top: 18px;">Order Line Items</div>
    <table class="order-line-table">
      <thead>
        <tr>
          <th>Product</th>
          <th class="qty">Qty</th>
          <th class="price">Price</th>
          <th class="subtotal">Subtotal</th>
          <th>
            <button class="line-add" type="button" onclick={addLineItem} title="Add">＋</button>
          </th>
        </tr>
      </thead>
      <tbody>
        {#each order.lineItems as item, idx}
          <tr>
            <td>
                <input list="products" bind:value={item.product} placeholder="Product" class="prod-cell" />
              
              <datalist id="products">
                {#each sampleProducts as p}
                  <option value={p}></option>
                {/each}
              </datalist>
            </td>
            <td>
                <input type="number" min="1" step="1" bind:value={item.quantity} class="num-cell" />
              
            </td>
            <td>

                <input type="number" min="0" step="0.01" bind:value={item.price} class="num-cell" />

              
            </td>
            <td class="subtotal">${lineItemTotal(item).toFixed(2)}</td>
            <td>
              <button class="line-del" type="button" onclick={() => removeLineItem(idx)} title="Remove">&times;</button>
            </td>
          </tr>
        {/each}
      </tbody>
      <tfoot>
        <tr class="total-row">
          <td colspan="3" style="border: none; text-align:right; font-weight:600;">Total:</td>
          <td class="subtotal" style="font-weight:700">${orderTotal().toFixed(2)}</td>
          <td style="border: none;"></td>
        </tr>
      </tfoot>
    </table>
  </section>

  <!-- RIGHT: Rules -->
  <section class="rules-section">
    <div class="rules-header">
      <span>Rules</span>
      <button type="button" class="check-btn" onclick={checkRules} title="Check rules">Check Rules</button>
    </div>

    <div class="rule-add">
        <input type="text" placeholder="Write a rule..." bind:value={newRuleInput} onkeydown={e => { if (e.key === 'Enter') addRule(); }} />

     
      <button type="button" class="add-btn" onclick={addRule}>Add Rule</button>
    </div>

    <div class="rules-list">
      {#if rules.length === 0}
        <div class="no-rules">No rules yet. Add your first rule above.</div>
      {/if}

      {#each rules as rule, idx}
        <div class="rule-card {rule.stub === 'fail' ? 'fail' : rule.stub === 'pass' ? 'pass' : ''}">
          <div class="rule-card-main" onclick={() => toggleRuleExpand(idx)}>
            <span class="rule-controls">
              <button class="icon-btn" title="Move up" disabled={idx === 0} onclick={e => { e.stopPropagation(); moveRule(idx, -1); }}>↑</button>
              <button class="icon-btn" title="Move down" disabled={idx === rules.length - 1} onclick={e => { e.stopPropagation(); moveRule(idx, 1); }}>↓</button>
            </span>

            <span class="rule-desc">{rule.description}</span>

            {#if rule.stub === 'pass'}
              <span class="stub pass-stub" title="Rule passes">✓</span>
            {:else if rule.stub === 'fail'}
              <span class="stub fail-stub" title="Rule fails">✗</span>
            {:else}
              <span class="stub neutral-stub" title="Not evaluated">•</span>
            {/if}

            <button class="icon-btn danger" title="Delete rule" onclick={e => { e.stopPropagation(); removeRule(idx); }}>&times;</button>
          </div>

          {#if rule.expanded}
            <div class="rule-details">
              <div><strong>Created by:</strong> {rule.user}</div>
              <div><strong>Created:</strong> {rule.created}</div>
              <div class="hint">This area can show parsed rule details, parameters, and any LLM interpretation.</div>
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </section>
</main> 
{/snippet}
</WindowFrame>

<style> /* Root layout inside window */ .order-editor-root { display: grid; grid-template-columns: 1.4fr 1fr; gap: 14px; height: 100%; background: linear-gradient(180deg, #f8fbff 0%, #f5f7fb 100%); padding: 8px; } /* Left panel */ .order-section { display: grid; grid-template-rows: auto auto 1fr; gap: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; overflow: auto; } /* Right panel */ .rules-section { display: grid; grid-template-rows: auto auto 1fr; gap: 12px; padding: 12px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; overflow: auto; } /* Headers */ .form-header { font-weight: 700; color: #0f172a; font-size: 1rem; } .rules-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-weight: 700; color: #0f172a; font-size: 1rem; } /* Grid for top form rows */ .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; } .form-group { display: grid; gap: 6px; } .form-group.label-right > label { justify-self: end; } .form-group.span-2 { grid-column: span 2; } /* Inputs */ .input-lg, .prod-cell, .num-cell, .rule-add input { width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 10px; background: #fff; outline: none; transition: border-color 120ms, box-shadow 120ms; } .input-lg:focus, .prod-cell:focus, .num-cell:focus, .rule-add input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.16); } /* Product chips */ .prod-chips { position: relative; display: flex; flex-wrap: wrap; gap: 8px; padding: 8px; border: 1px dashed #d1d5db; border-radius: 10px; background: #fbfdff; } .chip { display: inline-flex; align-items: center; gap: 6px; padding: 6px 10px; background: #eef3ff; color: #1e3a8a; border: 1px solid #d7e2ff; border-radius: 999px; font-weight: 600; font-size: 0.9rem; } .chip-del { border: none; background: transparent; color: #1e3a8a; cursor: pointer; font-size: 1rem; } .chip-input { min-width: 160px; border: none; outline: none; padding: 6px 8px; background: transparent; } .prod-dropdown { position: absolute; left: 8px; right: 8px; top: 100%; margin-top: 6px; border: 1px solid #e5e7eb; border-radius: 8px; background: #fff; box-shadow: 0 8px 18px rgba(0,0,0,0.08); z-index: 10; max-height: 180px; overflow: auto; } .prod-opt { padding: 8px 10px; cursor: pointer; } .prod-opt:hover { background: #f1f5ff; } /* Line items table */ .order-line-table { width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; background: #fff; } .order-line-table th, .order-line-table td { border-bottom: 1px solid #eef0f3; padding: 8px 10px; vertical-align: middle; } .order-line-table thead th { background: #f6f9ff; font-weight: 700; color: #0f172a; } .order-line-table .qty { width: 90px; } .order-line-table .price { width: 120px; } .order-line-table .subtotal { width: 120px; text-align: right; } .line-add, .line-del { border: 1px solid #d1d5db; background: #fff; border-radius: 8px; padding: 4px 8px; cursor: pointer; } .line-del { color: #b91c1c; } .line-add:hover, .line-del:hover { background: #f1f5ff; } .total-row td { background: #f9fbff; } /* Rules area */ .rule-add { display: grid; grid-template-columns: 1fr auto; gap: 8px; } .add-btn, .check-btn { padding: 8px 12px; border-radius: 10px; border: 1px solid #1d4ed8; background: #2563eb; color: #fff; font-weight: 700; cursor: pointer; } .add-btn:hover, .check-btn:hover { filter: brightness(1.05); } .rules-list { display: grid; gap: 10px; overflow: auto; } .no-rules { padding: 10px; color: #64748b; border: 1px dashed #cbd5e1; border-radius: 10px; background: #f8fafc; } /* Rule card */ .rule-card { border: 1px solid #e5e7eb; border-radius: 12px; background: #ffffff; box-shadow: 0 3px 12px rgba(0,0,0,0.04); } .rule-card.pass { border-color: #8dd99d; box-shadow: 0 4px 12px rgba(13,148,136,0.12); } .rule-card.fail { border-color: #f2a7a7; box-shadow: 0 4px 12px rgba(185,28,28,0.12); } .rule-card-main { display: grid; grid-template-columns: auto 1fr auto auto; gap: 10px; align-items: center; padding: 10px 12px; cursor: pointer; } .rule-controls { display: flex; gap: 6px; } .icon-btn { border: 1px solid #d1d5db; background: #fff; border-radius: 8px; padding: 4px 8px; cursor: pointer; } .icon-btn:disabled { opacity: 0.5; cursor: not-allowed; } .icon-btn.danger { color: #b91c1c; } .rule-desc { color: #0f172a; font-weight: 600; } .stub { font-weight: 800; display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 999px; border: 1px solid #d1d5db; background: #fff; } .pass-stub { color: #0f766e; border-color: #0f766e; } .fail-stub { color: #b91c1c; border-color: #b91c1c; } .neutral-stub { color: #64748b; border-color: #cbd5e1; } .rule-details { border-top: 1px solid #eef0f3; padding: 10px 12px; background: #fbfdff; color: #334155; font-size: 0.95rem; } .rule-details .hint { margin-top: 6px; font-size: 0.9rem; color: #64748b; } </style>
