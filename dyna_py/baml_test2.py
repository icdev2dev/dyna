from baml_client.async_client import b
from baml_client.types import StepFrameIn, StepFrameOut

async def tell_a_joke_v2(subject="foot", guidance="") -> StepFrameOut:
    in_arg = StepFrameIn(context=subject, guidance=guidance )
    return await b.TellAJokeV2(in_arg=in_arg)






