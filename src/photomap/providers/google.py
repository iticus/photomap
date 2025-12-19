"""
Created on 2025-12-10

@author: iticus
"""

import aiohttp


async def get_access_token(code: str, client_id: str, client_secret: str) -> str:
    session = aiohttp.ClientSession()
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "postmessage",
        "grant_type": "authorization_code"
    }
    response = await session.post("https://oauth2.googleapis.com/token", data=data, headers=headers)
    result = await response.json()
    await session.close()
    import json
    with open("/home/iticus/test_tokens.json", "w") as fl:
        fl.write(json.dumps(result))
    return {"access_token": result["access_token"], "refresh_token": result["refresh_token"]}


async def get_photos(auth_token: str) -> list[dict]:
    url = "https://photoslibrary.googleapis.com/v1/mediaItems"
    items = []
    params = {"pageSize": 100}
    session = aiohttp.ClientSession()
    while True:
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/json"
        }
        response = await session.get(url, headers=headers, params=params)
        data = await response.json()
        items.extend(data["mediaItems"])
        if data.get("nextPageToken"):
            params["nextPageToken"] = data["nextPageToken"]
        else:
            break
    await session.close()
    return items
