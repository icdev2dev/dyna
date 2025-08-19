from fastmcp import Client
import asyncio

# Define the MCP server configuration
CONFIG = {
    "mcpServers": {
        "aws-knowledge-mcp-server": { "url": "https://knowledge-mcp.global.api.aws"}
    }
}

CACHE_TOOLS = {
    "aws_kb_search": "aws___search_documentation"
}


CLIENT = Client(CONFIG)

async def async_input(prompt: str = '') -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input, prompt)



async def list_tools(client): 
    async with client:
        try :
            tools  = await client.list_tools()
            for tool in tools:
                print(tool.name)
                print (f"         {tool.description}")
        except Exception as e:
            print(e)


async def search_aws_kb (client, tool_name, user_input) -> str:
    async with client:
        try :
            result = await client.call_tool(tool_name, {
                "search_phrase": f"{user_input}"
            })
            import json
            result = json.loads(result.content[0].text)['response']['payload']['content']['result']

            return str(result)
        
        except Exception as e:
            return str(e)
        
        
async def main():

#        await list_tools(CLIENT)


    while True:

        input_text = await async_input()
        search_result = await search_aws_kb(CLIENT,CACHE_TOOLS['aws_kb_search'], input_text )
        print(search_result)

if __name__ == "__main__":
    asyncio.run(main())