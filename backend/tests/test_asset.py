def make_asset(**overrides):
    data = {
        "asset_no": "ZC100",
        "name": "测试资产",
        "category": "电脑设备",
        "brand": "TestBrand",
        "model": "T-1",
        "price": 1000.0,
        "purchase_date": "2024-01-01",
        "status": "空闲",
        "user_id": None,
        "remark": "测试数据",
    }
    data.update(overrides)
    return data


def test_create_asset_ok(client):
    resp = client.post("/api/asset", json=make_asset())
    body = resp.json()
    assert resp.status_code == 200
    assert body["code"] == 200
    assert body["msg"] == "新增成功"
    assert body["data"]["asset_no"] == "ZC100"


def test_create_asset_missing_name(client):
    data = make_asset()
    del data["name"]
    resp = client.post("/api/asset", json=data)
    assert resp.status_code == 422
    assert "名称" in resp.json()["msg"]


def test_create_asset_negative_price(client):
    resp = client.post("/api/asset", json=make_asset(price=-5))
    assert resp.status_code == 422
    assert "价格" in resp.json()["msg"]


def test_create_asset_bad_status(client):
    resp = client.post("/api/asset", json=make_asset(status="随便填"))
    assert resp.status_code == 422
    assert "状态" in resp.json()["msg"]


def test_create_duplicate_asset_no(client):
    assert client.post("/api/asset", json=make_asset()).status_code == 200
    resp = client.post("/api/asset", json=make_asset(name="另一个资产"))
    assert resp.status_code == 400
    assert resp.json()["msg"] == "资产编号已存在，请更换后重试"


def test_create_duplicate_asset_name(client):
    assert client.post("/api/asset", json=make_asset()).status_code == 200
    resp = client.post("/api/asset", json=make_asset(asset_no="ZC200"))
    assert resp.status_code == 400
    assert resp.json()["msg"] == "资产名称已存在，请勿重复录入"


def test_list_pagination_and_filter(client):
    for i in range(3):
        client.post(
            "/api/asset",
            json=make_asset(asset_no=f"ZC10{i}", name=f"资产{i}", status="空闲" if i < 2 else "维修"),
        )
    resp = client.get("/api/asset/list", params={"page": 1, "size": 2})
    body = resp.json()
    assert body["data"]["total"] == 3
    assert len(body["data"]["items"]) == 2
    assert "create_time" not in body["data"]["items"][0]

    resp = client.get("/api/asset/list", params={"status": "空闲"})
    assert resp.json()["data"]["total"] == 2

    resp = client.get("/api/asset/list", params={"name": "资产1"})
    assert resp.json()["data"]["total"] == 1


def test_get_asset_and_404(client):
    aid = client.post("/api/asset", json=make_asset()).json()["data"]["id"]
    resp = client.get(f"/api/asset/{aid}")
    assert resp.json()["data"]["name"] == "测试资产"

    resp = client.get("/api/asset/999")
    assert resp.status_code == 404
    assert resp.json()["msg"] == "资产不存在"


def test_update_asset_and_clear_user(client):
    aid = client.post("/api/asset", json=make_asset(status="已领用", user_id=1)).json()["data"]["id"]
    resp = client.put(f"/api/asset/{aid}", json={"user_id": None, "status": "空闲"})
    body = resp.json()
    assert body["msg"] == "修改成功"
    assert body["data"]["user_id"] is None
    assert body["data"]["status"] == "空闲"


def test_update_duplicate_asset_no(client):
    aid = client.post("/api/asset", json=make_asset()).json()["data"]["id"]
    client.post("/api/asset", json=make_asset(asset_no="ZC200", name="二号资产"))
    resp = client.put(f"/api/asset/{aid}", json={"asset_no": "ZC200"})
    assert resp.status_code == 400
    assert resp.json()["msg"] == "资产编号已存在，请更换后重试"


def test_delete_asset(client):
    aid = client.post("/api/asset", json=make_asset()).json()["data"]["id"]
    resp = client.delete(f"/api/asset/{aid}")
    assert resp.json()["msg"] == "删除成功"
    assert client.get(f"/api/asset/{aid}").status_code == 404
