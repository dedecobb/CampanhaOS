"""
Teste do endpoint de health check.

Este é o primeiro teste do projeto — propositalmente simples. Sua função
é validar que a estrutura de testes (pytest + httpx + TestClient) funciona
de ponta a ponta, servindo de modelo para os testes dos módulos seguintes.
"""

from fastapi.testclient import TestClient

from src.presentation.api.main import app

client = TestClient(app)


def test_health_check_returns_ok() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
