import RenderForm from './RenderForm.svelte';
import RenderChat from './RenderChat.svelte';
import RenderMetadata from './RenderMetadata.svelte';
import RenderPlugin from '../RenderPlugin.svelte';
import RenderAgentsList from './RenderAgentsList.svelte';
import RenderOrderEditor from './RenderOrderEditor.svelte';
import RenderAgentRuns from './RenderAgentRuns.svelte';
import RenderRunDetail from './RenderRunDetail.svelte';
import LiveRunRenderer from './RenderLiveRun.svelte';
import RenderConversations from './RenderConversations.svelte';
import RenderConversationThread from './RenderConversationThread.svelte';
import RenderAgentSessions from './RenderAgentSessions.svelte';
import RenderAgentConfigs from './RenderAgentConfigs.svelte';
import RenderTaskGraph from './RenderTaskGraph.svelte';

import RenderJokeAgentRun from './RenderJokeAgentRun.svelte';
import RenderGoalAgentRun from './RenderGoalAgentRun.svelte';

export const WINDOW_RENDERERS = {
    form: RenderForm,
    chat: RenderChat,
    metadata: RenderMetadata,
    plugin: RenderPlugin,
    agentsList: RenderAgentsList,
    orderEditor: RenderOrderEditor,
    agentRuns: RenderAgentRuns,
    runDetail: RenderRunDetail,
    liveRun: LiveRunRenderer,
    conversations: RenderConversations,
    conversationThread: RenderConversationThread,
    agentSessions: RenderAgentSessions,
    agentConfigs: RenderAgentConfigs, 
    taskGraph: RenderTaskGraph,
    jokeAgentRun: RenderJokeAgentRun,
    goalAgentRun: RenderGoalAgentRun
};
