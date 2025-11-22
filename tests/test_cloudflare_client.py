import asyncio
import pytest
from app.cloudflare_client import CloudflareClient

@pytest.mark.asyncio
async def test_invalid_token_raises():
    client = CloudflareClient("invalid-token")
    with pytest.raises(Exception):
        await client.list_zones()
    await client.close()
