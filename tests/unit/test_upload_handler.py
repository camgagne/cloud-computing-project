import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

UPLOAD_DIR = str(Path(__file__).resolve().parents[2] / "lambda_functions" / "upload")


@pytest.fixture
def upload_handler(monkeypatch):
    monkeypatch.setenv("BUCKET_NAME", "test-image-bucket")
    monkeypatch.syspath_prepend(UPLOAD_DIR)

    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://s3.example/presigned-put"

    sys.modules.pop("handler", None)
    with patch("boto3.client", return_value=mock_s3):
        handler = importlib.import_module("handler")
        yield handler, mock_s3
    sys.modules.pop("handler", None)


def _event(token_use="access", sub="user-123", body=None):
    return {
        "requestContext": {
            "authorizer": {
                "jwt": {
                    "claims": {
                        "token_use": token_use,
                        "sub": sub,
                    }
                }
            }
        },
        "body": json.dumps(body) if body is not None else None,
    }


def test_handler_rejects_non_access_token(upload_handler):
    handler, mock_s3 = upload_handler

    response = handler.handler(_event(token_use="id"), None)

    assert response["statusCode"] == 403
    assert json.loads(response["body"]) == {"error": "Access token required"}
    mock_s3.generate_presigned_url.assert_not_called()


def test_handler_rejects_invalid_content_type(upload_handler):
    handler, mock_s3 = upload_handler

    response = handler.handler(
        _event(body={"contentType": "image/gif"}),
        None,
    )

    assert response["statusCode"] == 400
    assert json.loads(response["body"]) == {"error": "Invalid image type"}
    mock_s3.generate_presigned_url.assert_not_called()


def test_handler_returns_presigned_url_for_png(upload_handler):
    handler, mock_s3 = upload_handler

    response = handler.handler(
        _event(sub="user-abc", body={"contentType": "image/png"}),
        None,
    )

    assert response["statusCode"] == 200
    payload = json.loads(response["body"])
    assert payload["uploadUrl"] == "https://s3.example/presigned-put"
    assert payload["imageKey"].startswith("posts/user-abc/")
    assert payload["imageKey"].endswith(".png")

    mock_s3.generate_presigned_url.assert_called_once()
    _, kwargs = mock_s3.generate_presigned_url.call_args
    assert kwargs["Params"]["Bucket"] == "test-image-bucket"
    assert kwargs["Params"]["Key"] == payload["imageKey"]
    assert kwargs["Params"]["ContentType"] == "image/png"


@pytest.mark.parametrize(
    "content_type,extension",
    [
        ("image/jpeg", "jpg"),
        ("image/webp", "webp"),
    ],
)
def test_handler_maps_content_type_to_extension(
    upload_handler, content_type, extension
):
    handler, mock_s3 = upload_handler

    response = handler.handler(
        _event(sub="user-xyz", body={"contentType": content_type}),
        None,
    )

    assert response["statusCode"] == 200
    image_key = json.loads(response["body"])["imageKey"]
    assert image_key.startswith("posts/user-xyz/")
    assert image_key.endswith(f".{extension}")
    mock_s3.generate_presigned_url.assert_called_once()
