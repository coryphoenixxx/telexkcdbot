async def test_hello(client):
    resp = await client.get("/api")
    assert resp.status == 200


async def test_create_comic(client):
    comic = {
        "comic_id": 10,
        "publication_date": "08-05-2006",
        "is_specific": False,
        "translations": [
            {
                "language_code": "ru",
                "title": "ru_title",
                "image_url": "ru_image_url",
                "comment": "ru_comment",
                "transcript": "ru_transcript",
            },
            {
                "language_code": "en",
                "title": "en_title",
                "image_url": "en_img_url",
                "comment": "en_comment",
                "transcript": "en_transcript",
            },
        ],
    }

    resp = await client.post("/api/comics", json=comic)
    assert resp.status == 201
