

function JokeTeller(arg:string) -> string {
    client CustomGPT4oMini    
    prompt #"

        {{ctx.output_format}}

        {{arg}}
        
    "#
}


class MonikerState {
    topic string?          // generic focus of the task (formerly "subject"); optional for broad tasks
    last_style string?     // last style/tone used (generic)
    last_output string?    // last emitted human-facing text (generic)
}

class MonikerGuidance {
    topic string? @description(#"
        optional one-shot override for topic
    "#)         
    style string?  @description(#"
        optional style/tone hint (e.g., "dry", "formal", "playful")
    "#)         
}

class MonikerData {
    topic string? @description(#"
     simple structured echo for consumers; extend as needed
        
    "#)         
}

class MonikerStepFrameIn {
    step string 
    state MonikerState
    guidance MonikerGuidance?
}

class MonikerStepFrameOut {
    step string
    state MonikerState
    next_step string
    
    text string @description(#"
        human-facing output for this step
    "#)           
    data MonikerData @description(#"
        structured output (minimal, extendable)
    "#)      
    done bool @description(#"
        true when the moniker’s workflow is complete
    "#)             
    notes string?  @description(#"
         short rationale/what changed
    "#)        
}

// Generic moniker runner: provide the task description + a StepFrame input.
// Examples of task: 
//  - "Tell a short witty joke about the topic."
//  - "Write a two-sentence summary of the topic."
//  - "List three key facts about the topic."


function TellAJoke(frame: MonikerStepFrameIn, task: string)-> MonikerStepFrameOut  {
    client CustomGPT4oMini
    prompt #"
         You are a moniker that performs exactly one step of work according to 'task'.

        {{ctx.output_format}}

        Requirements:
        - Perform the task based on state and (if present) guidance.
        - If guidance.topic is present, use it and update state.topic.
        - If guidance.style is present, reflect it in the output and set state.last_style.
        - Place the human-facing output in 'text'.
        - Set data.topic to the final topic used for this step.
        - Set state.last_output to the same 'text' value.
        - Echo back the input 'step' as 'step'.
        - set next_step to be the next step as indicated.
        - Set 'done' true only if the task is inherently single-shot or indicates completion; otherwise false.
        - Do not add extra keys or commentary.
        
        # step 0:
        - keep telling jokes
        # step 1
        - tell bigger jokes
        - next_step 2.1
        # step 2.1
        - tell sad joke
        - next_step 2.2
        # step 2.2
        - tell sad joke
        - next_step 3
        
        # step 3
        - ok we are done

        -- TASK --
        {{ task }}
        -- END TASK --

        -- INPUT FRAME --
        {{ frame }}
        -- END INPUT FRAME --
    "#
}