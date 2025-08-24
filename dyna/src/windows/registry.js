import RenderForm from './RenderForm.svelte';
import RenderChat from './RenderChat.svelte';
import RenderMetadata from './RenderMetadata.svelte';
import RenderPlugin from '../RenderPlugin.svelte';
import RenderAgentsList from './RenderAgentsList.svelte';
import RenderOrderEditor from './RenderOrderEditor.svelte';

export const WINDOW_RENDERERS = {
    form: RenderForm,
    chat: RenderChat,
    metadata: RenderMetadata,
    plugin: RenderPlugin,
    agentsList: RenderAgentsList,
    orderEditor: RenderOrderEditor  
};
