import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.models import db


@pytest.fixture()
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        },
    })
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_create_and_get(client):
    response = client.post("/api/clientes", json={
        "nome": "Teste",
        "email": "teste@example.com",
        "cpf": "11111111111",
        "cidade": "Santa Maria",
        "idade": 21,
    })
    assert response.status_code == 201
    cliente_id = response.get_json()["id"]

    response = client.get(f"/api/clientes/{cliente_id}")
    assert response.status_code == 200
    assert response.get_json()["nome"] == "Teste"


def test_update(client):
    response = client.post("/api/clientes", json={
        "nome": "Teste",
        "email": "teste2@example.com",
        "cpf": "22222222222",
        "cidade": "Santa Maria",
        "idade": 21,
    })
    cliente_id = response.get_json()["id"]

    response = client.put(f"/api/clientes/{cliente_id}", json={"idade": 30})
    assert response.status_code == 200
    assert response.get_json()["idade"] == 30


def test_delete(client):
    response = client.post("/api/clientes", json={
        "nome": "Teste",
        "email": "teste3@example.com",
        "cpf": "33333333333",
        "cidade": "Pelotas",
        "idade": 21,
    })
    cliente_id = response.get_json()["id"]

    response = client.delete(f"/api/clientes/{cliente_id}")
    assert response.status_code == 200
    assert client.get(f"/api/clientes/{cliente_id}").status_code == 404
