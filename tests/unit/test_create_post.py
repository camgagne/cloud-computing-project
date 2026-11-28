import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND_DIR = str(Path(__file__).resolve().parents[2] / "backend")


@pytest.fixture
def create_post_module(monkeypatch):
    monkeypatch.setenv("POSTS_TABLE", "Posts")
    monkeypatch.setenv("USERS_TABLE", "Users")
    monkeypatch.syspath_prepend(BACKEND_DIR)

    mock_posts = MagicMock()
    mock_users = MagicMock()
    mock_sns = MagicMock()

    def table_for(name):
        return mock_posts if name == "Posts" else mock_users

    mock_resource = MagicMock()
    mock_resource.Table.side_effect = table_for

    # Clear any previously imported module so env + mocks apply cleanly
    for name in list(sys.modules):
        if name == "posts" or name.startswith("posts."):
            sys.modules.pop(name, None)

    with patch("boto3.resource", return_value=mock_resource), patch(
        "boto3.client", return_value=mock_sns
    ):
        create_post = importlib.import_module("posts.create_post")
        yield create_post, mock_posts, mock_users, mock_sns

    for name in list(sys.modules):
        if name == "posts" or name.startswith("posts."):
            sys.modules.pop(name, None)


def _event(user_id="user-1", image_key="posts/user-1/img.png", caption="hello"):
    return {
        "requestContext": {
            "authorizer": {"jwt": {"claims": {"sub": user_id}}}
        },
        "body": json.dumps({"imageKey": image_key, "caption": caption}),
    }


def test_create_post_publishes_sns_confirmation(create_post_module):
    create_post, mock_posts, mock_users, mock_sns = create_post_module
    mock_users.get_item.return_value = {
        "Item": {
            "userId": "user-1",
            "snsTopicArn": "arn:aws:sns:us-east-1:123:post-created-user-1",
        }
    }

    response = create_post.handler(_event(), None)

    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    mock_posts.put_item.assert_called_once()
    mock_sns.publish.assert_called_once()
    publish_kwargs = mock_sns.publish.call_args.kwargs
    assert publish_kwargs["TopicArn"] == "arn:aws:sns:us-east-1:123:post-created-user-1"
    assert publish_kwargs["Subject"] == "Your post was created"
    assert body["postId"] in publish_kwargs["Message"]
    assert "hello" in publish_kwargs["Message"]


def test_create_post_skips_sns_when_no_topic(create_post_module):
    create_post, mock_posts, mock_users, mock_sns = create_post_module
    mock_users.get_item.return_value = {"Item": {"userId": "user-1"}}

    response = create_post.handler(_event(), None)

    assert response["statusCode"] == 201
    mock_posts.put_item.assert_called_once()
    mock_sns.publish.assert_not_called()


def test_create_post_rejects_invalid_image_key(create_post_module):
    create_post, mock_posts, mock_users, mock_sns = create_post_module

    response = create_post.handler(
        _event(image_key="posts/other-user/img.png"),
        None,
    )

    assert response["statusCode"] == 400
    mock_posts.put_item.assert_not_called()
    mock_sns.publish.assert_not_called()
