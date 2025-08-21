<script> 
    let { who = 'world' } = $props(); 
    let count = $state(0); 
    const inc = () => (count += 1); 
</script> 
<div style="padding:8px"> 
    <h2>Hello, {who}!</h2> <p>Count: {count}</p> 
    <button onclick={inc}>Increment</button> 
</div>
