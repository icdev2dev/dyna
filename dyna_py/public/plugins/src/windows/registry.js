import RenderForm from './RenderForm.svelte';
import RenderChat from './RenderChat.svelte';
import RenderMetadata from './RenderMetadata.svelte';
import RenderPlugin from '../RenderPlugin.svelte';
export const WINDOW_RENDERERS = {
    form: RenderForm,
    chat: RenderChat,
    metadata: RenderMetadata,
    plugin: RenderPlugin
    
};
