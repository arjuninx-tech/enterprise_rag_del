from io import BytesIO
from unittest import TestCase
from uuid import uuid4

from onprem_rag.server import flask_app


class ServerBoundaryTests(TestCase):
    def setUp(self):
        self.client = flask_app.test_client()

    def test_web_api_rejects_non_allowlisted_method(self):
        response = self.client.post(
            "/api/_set_window",
            json=[],
            headers={"X-Client-ID": str(uuid4())},
        )
        self.assertEqual(response.status_code, 403)

    def test_web_api_requires_client_id(self):
        response = self.client.post("/api/get_chats", json=[])
        self.assertEqual(response.status_code, 400)

    def test_upload_rejects_unsupported_file(self):
        response = self.client.post(
            "/api/upload_attachment",
            data={
                "chat_id": "example",
                "file": (BytesIO(b"content"), "payload.exe"),
            },
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 415)
