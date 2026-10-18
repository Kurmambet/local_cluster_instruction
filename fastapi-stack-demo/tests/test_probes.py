import httpx

from src.main import app


async def test_livez_does_not_need_dependencies() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/livez")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
