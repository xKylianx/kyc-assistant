from io import BytesIO

from fastapi.testclient import TestClient

from src.api.main import app


def test_upload_health_and_root():
    with TestClient(app) as client:
        assert client.get('/').status_code == 200
        assert client.get('/files/health').json()['status'] == 'ok'


def test_upload_returns_prep_state():
    csv = b"Nom,Prenom,DOB,Status,ID Type,ID Number,Address,City\nDoe,Jane,1990-01-01,Active,ID,ABC123,1 Rue Paris,Paris\n"
    with TestClient(app) as client:
        response = client.post(
            '/files/upload',
            files={'file': ('e2e.csv', BytesIO(csv), 'text/csv')},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'success'
    assert payload['file']['file_id']
    assert payload['prep_state']['file_id'] == payload['file']['file_id']
    assert payload['prep_state']['prep_status'] == 'uploaded'
