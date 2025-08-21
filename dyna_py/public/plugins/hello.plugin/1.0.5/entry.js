import { mount } from 'svelte';   
  import Comp from './compiled.js';   
  export default Comp;   // Use the plugin's bundled runtime to mount its function component   
  export function mountPlugin(target, props = {}) {     return mount(Comp, { target, props });   }