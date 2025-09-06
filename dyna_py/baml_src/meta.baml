enum RegisteredWindow {
    AgentConfigsWindow @description(#"
        This is the window that let you add / update / delete different types of agents including JokeAgent 
        and PersonaAgent
    "#)
    AgentsListWindow @description(#"
        This is the window that lets you see all the different agents that you can act on.
    "#)

    ConversationsWindow @description(#"
        This is the window that lets you see all the conversations associated in a multi-agent scenario.
    "#)
}

function GetRegisteredWindow(in_arg: string) -> RegisteredWindow {
    client CustomGPT4o
    prompt #"
        This returns the registered window from a given string.
        {{ctx.output_format}}

        ---- GIVEN STRING ---
        {{in_arg}}
        ---- END GIVEN STRING ---
        
    "#
}