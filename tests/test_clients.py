def test_deactivate_client(db):
        from app.models.client import Client
        from app.repositories.client_repo import deactivate_client

        client = Client(name="Pedro", phone="123", is_active=True)
        db.add(client)
        db.commit()

        deactivate_client(db, client)

        assert client.is_active is False
