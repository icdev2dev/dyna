from baml_client.async_client import b


async def tell_a_joke(subject="foot") -> str:
    return await b.JokeTeller(f"tell a joke about john using subject {subject}")


