from baml_client.async_client import b
from baml_client.types import MonikerStepFrameIn, MonikerStepFrameOut, MonikerGuidance, MonikerState
from baml_client.types import StepFrameIn, StepFrameOut
async def tell_a_joke(subject="foot") -> str:
    initial_state = MonikerState()
    guidance = MonikerGuidance(topic="dogs")
    a = MonikerStepFrameIn(step="0", state=initial_state,guidance=guidance)
    joke_text = f"tell a joke about john on the subject of {subject}"
    return await  b.TellAJoke(a, joke_text)


async def tell_a_joke_v2(subject="foot", guidance="") -> str:
    in_arg = StepFrameIn(context=subject, guidance=guidance )
    return await b.TellAJokeV2(in_arg=in_arg)






