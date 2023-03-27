# -*- coding: utf-8 -*-
import pytest
from fastapi.testclient import TestClient
from keycloak.uma_permissions import AuthStatus
from typing import Tuple, Any


@pytest.fixture
def init_test_client(monkeypatch) -> TestClient:
    def mock_make_inference(*args, **kwargs) -> dict[str, float]:
        return {"mpg": 48.239}

    def mock_load_model(*args, **kwargs) -> None:
        return None

    def mock_keycloak_openid(*args, **kwargs) -> Any:
        class FakedKeycloakOpenID:
            @staticmethod
            def well_known(*args, **kwargs):
                return {"token_endpoint": "fakedendpoint"}

            @staticmethod
            def has_uma_access(token: str, *args, **kwargs) -> AuthStatus:
                if token == "Ok":
                    return AuthStatus(True, True, set())
                elif token == "Not_logged":
                    return AuthStatus(False, False, set())
                elif token == "Not_authorized":
                    return AuthStatus(True, False, set())
                else:
                    return AuthStatus(False, False, set())
        return FakedKeycloakOpenID

    monkeypatch.setenv("MODEL_PATH", "faked/model.pkl")
    monkeypatch.setenv("KEYCLOAK_URL", "fakeurl")
    monkeypatch.setenv("CLIENT_ID", "fakeid")
    monkeypatch.setenv("CLIENT_SECRET", "fakesecret")
    monkeypatch.setattr("model_utils.make_inference", mock_make_inference)
    monkeypatch.setattr("model_utils.load_model", mock_load_model)
    monkeypatch.setattr("keycloak.KeycloakOpenID", mock_keycloak_openid)

    from main import app
    return TestClient(app)


def test_healthcheck(init_test_client) -> None:
    response = init_test_client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_token_correctness(init_test_client) -> None:
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer Ok"},
        json={"cylinders": 0, "displacement": 0, "horsepower": 0,
              "weight": 0, "acceleration": 0, "model_year": 0, "origin": 0}
    )
    assert response.status_code == 200
    assert "mpg" in response.json()


def test_token_not_correctness(init_test_client):
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer Not_logged"},
        json={"cylinders": 0, "displacement": 0, "horsepower": 0,
              "weight": 0, "acceleration": 0, "model_year": 0, "origin": 0}
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid authentication credentials"
    }


def test_access_denied(init_test_client):
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer Not_authorized"},
        json={"cylinders": 0, "displacement": 0, "horsepower": 0,
              "weight": 0, "acceleration": 0, "model_year": 0, "origin": 0}
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": "Access denied"
    }


def test_token_absent(init_test_client):
    response = init_test_client.post(
        "/predictions",
        json={"cylinders": 0, "displacement": 0, "horsepower": 0,
              "weight": 0, "acceleration": 0, "model_year": 0, "origin": 0}
    )
    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }


def test_inference(init_test_client):
    response = init_test_client.post(
        "/predictions",
        headers={"Authorization": "Bearer Ok"},
        json={"cylinders": 4, "displacement": 113.0, "horsepower": 95.0,
              "weight": 2228.0, "acceleration": 14.0, "model_year": 71,
              "origin": 3}
    )
    assert response.status_code == 200
    assert response.json()["mpg"] == 48.239
