def _create_three_level_tree(client):
    root = client.post("/departments/", json={"name": "HQ"}).json()
    eng = client.post(
        "/departments/",
        json={"name": "Engineering", "parent_id": root["id"]},
    ).json()
    backend = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": eng["id"]},
    ).json()
    return root, eng, backend


def test_depth_default_includes_direct_children_only(client) -> None:
    root, eng, backend = _create_three_level_tree(client)

    response = client.get(f"/departments/{root['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == "Engineering"
    assert data["children"][0]["children"] == []
    assert client.get(f"/departments/{backend['id']}").status_code == 200


def test_depth_two_includes_grandchildren(client) -> None:
    root, _, _ = _create_three_level_tree(client)

    data = client.get(f"/departments/{root['id']}", params={"depth": 2}).json()
    assert len(data["children"]) == 1
    assert len(data["children"][0]["children"]) == 1
    assert data["children"][0]["children"][0]["name"] == "Backend"


def test_include_employees_false(client) -> None:
    root, eng, _ = _create_three_level_tree(client)
    client.post(
        f"/departments/{eng['id']}/employees/",
        json={"full_name": "Alice", "position": "Dev"},
    )

    data = client.get(
        f"/departments/{root['id']}",
        params={"depth": 2, "include_employees": False},
    ).json()
    assert data["employees"] == []
    assert data["children"][0]["employees"] == []


def test_create_department_with_missing_parent_returns_404(client) -> None:
    response = client.post(
        "/departments/",
        json={"name": "Orphan", "parent_id": 9999},
    )
    assert response.status_code == 404
    assert "родитель" in response.json()["detail"].lower()


def test_trim_whitespace_in_department_name(client) -> None:
    response = client.post(
        "/departments/",
        json={"name": "  Backend  "},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Backend"


def test_patch_name_only(client) -> None:
    dept = client.post("/departments/", json={"name": "Old"}).json()
    response = client.patch(
        f"/departments/{dept['id']}",
        json={"name": "New"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_patch_parent_id_only(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Team", "parent_id": root["id"]},
    ).json()
    response = client.patch(
        f"/departments/{child['id']}",
        json={"parent_id": None},
    )
    assert response.status_code == 200
    assert response.json()["parent_id"] is None


def test_reassign_without_target_returns_400(client) -> None:
    dept = client.post("/departments/", json={"name": "Sales"}).json()
    response = client.delete(f"/departments/{dept['id']}", params={"mode": "reassign"})
    assert response.status_code == 400
    assert "reassign_to_department_id" in response.json()["detail"]


def test_delete_invalid_mode_returns_422(client) -> None:
    dept = client.post("/departments/", json={"name": "Temp"}).json()
    response = client.delete(f"/departments/{dept['id']}", params={"mode": "invalid"})
    assert response.status_code == 422
