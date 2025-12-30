import asyncio
from fastmcp import Client
from fastmcp.client import StreamableHttpTransport

BASE_URL = "http://localhost:8001/sport/mcp"

async def test_list_tools():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        tools = await client.list_tools()
        print('tools', tools)
        print('tools list_tools_mcp', await client.list_tools_mcp())
        
        print(f"Total tools: {len(tools)}")
        for tool in tools:
            print(tool.name)

async def test_stand_up():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("stand_up", {})
        print(result)

async def test_stand_down():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("stand_down", {})
        print(result)

async def test_move_forward():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("move_forward", {})
        print(result)


async def test_turn_left():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("turn_left", {})
        print(result)

async def test_turn_right():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("turn_right", {})
        print(result)


async def test_move_backward():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("move_backward", {})
        print(result)


async def test_step_to_left():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("step_to_left", {})
        print(result)
        
async def test_step_to_right():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("step_to_right", {})
        print(result)

async def test_all_cmp_tools():
    await test_list_tools()
    await test_stand_up()
    # await test_move_forward()
    # await test_turn_left()
    # await test_turn_right()
    # await test_move_backward()
    # await test_stand_down()
    await test_step_to_left()
    # await asyncio.sleep(5)
    # await test_step_to_right()
if __name__ == "__main__":
    asyncio.run(test_all_cmp_tools())



