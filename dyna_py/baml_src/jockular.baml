enum GenericStepOutStatus {
    OK 
    ERR   
}
enum GenericStepOutControl {
    CONTINUE
    PAUSE
    STOP 
    DONE
}

class StepFrameIn {
    context string @description(#"
        This is an json encoded string input field to provide exact context of the task at hand. 
    "#)
    guidance string @description(#"
        This is an json encoded string input field and it will provide you additional guidance on a mutiple step workflow if required. 
    "#)
}

class StepFrameOut {
        
    status GenericStepOutStatus? @description(#"
        This is the status of the request. Generally ok.
    "#)
    control GenericStepOutControl? @description(#"
        This is to give you some agency to indicate to an outside loop that is 
        controlling your excecution on whether to continue, pause, stop or be done.

        Most of time your response would be to continue. 
        If anything else than continue, you will need to provide a reason
        If it is pause, you would also populate hints to indicate when to resume        
    "#)
    reason string? @description(#"
        if the decision is anything other than continue, then give reason.
    "#)
    hint string? @description(#"
        if the control is pause, then give some hint when to resume.
    "#)

    text string? @description(#"
        this is the human readable output 
    "#)
    payload string? @description(#"
        this is the structured output.
    "#)
    context_delta string? @description(#"
        You have been provided with some context and some guidance. 
        This is your interpretation of the consolidated context. 
        In the next iteration, this will be the changed context with no additional guidance IF this is different than the original context.
    "#)

}



function TellAJokeV2(in_arg:StepFrameIn)->StepFrameOut {
    client CustomGPT4oMini
    prompt #"
        Tell a joke about {{in_arg.context}} with following guidance if any: {{in_arg.guidance}}.

        {{ctx.output_format}}


    "#
}

