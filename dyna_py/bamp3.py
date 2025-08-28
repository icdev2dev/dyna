from baml_client.async_client import b
from baml_client.types import MonikerStepFrameIn, MonikerStepFrameOut, MonikerGuidance, MonikerState


async def tell_a_joke(subject="foot") -> str:
    initial_state = MonikerState()
    guidance = MonikerGuidance(topic="dogs")
    a = MonikerStepFrameIn(step="0", state=initial_state,guidance=guidance)
    joke_text = f"tell a joke about john on the subject of {subject}"
    return await  b.TellAJoke(a, joke_text)

