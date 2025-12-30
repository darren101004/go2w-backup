from fastmcp import Client
from fastmcp.client import StreamableHttpTransport
import asyncio
BASE_URL = "http://localhost:8001/camera/mcp"

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

async def test_capture_image():
    client = Client(
        transport=StreamableHttpTransport(url=BASE_URL)
    )
    async with client:
        assert client.is_connected()
        result = await client.call_tool("capture_image", {})
        assert result is not None
        image_data = result.structured_content["data"]
        import base64

        if image_data:
            img_bytes = base64.b64decode(image_data)
            with open("test_mcp_cam.jpg", "wb") as f:
                f.write(img_bytes)
            print("Image saved to test_mcp_cam.jpg")
        else:
            print("No image data to save.")

async def test_all_cmp_tools():
    await test_list_tools()
    await test_capture_image()
    
if __name__ == "__main__":
    asyncio.run(test_all_cmp_tools())