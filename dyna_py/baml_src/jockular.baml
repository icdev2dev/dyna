function JokeTeller(arg:string) -> string {
    client CustomGPT4oMini    
    prompt #"

        {{ctx.output_format}}

        {{arg}}
        
    "#
}