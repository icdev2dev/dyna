function Hello(inp_txt:string) -> string {
  client CustomGPT4oMini
  prompt #"
    Say something in response to input text
    {{ctx.output_format}}

    --------------
    {{inp_txt}}
    --------------
  "#
}

class Response {
  can_the_question_be_answered bool @description(#"
    ability of the question to be answered in the given context
  "#)
  raionale string @description(#"
    why the question can be answered or not
  "#)
}
function RAG(question: string, context: string) -> Response {
  client "openai/gpt-4o"
  prompt #"
    Answer the question in full sentences using the provided context.
    Do not make up an answer. If the information is not provided in the context, say so clearly. 
    Take some reasonable liberty with context. However do not interject your own knowledge. 
    If there's some background provided, use that to see if the context matches.
    Also if the context is more specific than the question, that is irrelevant.
    If there is something that matches the question, please mention that and do not provide further elaboration.
    
    QUESTION: {{ question }}
    RELEVANT CONTEXT: {{ context }}
    {{ ctx.output_format }}
      "# 
}

