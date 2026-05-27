def test_create_department_and_employee(client) -> None:
    root = client.post("/departments/", json={"name": "Company"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Engineering", "parent_id": root["id"]},
    ).json()

    employee_response = client.post(
        f"/departments/{child['id']}/employees/",
        json={"full_name": "Jane Doe", "position": "Developer", "hired_at": "2024-01-15"},
    )
    assert employee_response.status_code == 201
    employee = employee_response.json()
    assert employee["department_id"] == child["id"]
    assert employee["full_name"] == "Jane Doe"


def test_get_department_tree_with_depth(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    eng = client.post(
        "/departments/",
        json={"name": "Engineering", "parent_id": root["id"]},
    ).json()
    backend = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": eng["id"]},
    ).json()
    client.post(
        f"/departments/{backend['id']}/employees/",
        json={"full_name": "Alice", "position": "Engineer"},
    )

    response = client.get(f"/departments/{root['id']}", params={"depth": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["department"]["name"] == "HQ"
    assert len(data["children"]) == 1
    assert data["children"][0]["name"] == "Engineering"
    assert len(data["children"][0]["children"]) == 1
    assert data["children"][0]["children"][0]["name"] == "Backend"
    assert len(data["children"][0]["children"][0]["employees"]) == 1


def test_duplicate_department_name_conflict(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    first = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": root["id"]},
    )
    assert first.status_code == 201

    duplicate = client.post(
        "/departments/",
        json={"name": "Backend", "parent_id": root["id"]},
    )
    assert duplicate.status_code == 409


def test_move_department_cycle_conflict(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Engineering", "parent_id": root["id"]},
    ).json()

    response = client.patch(
        f"/departments/{root['id']}",
        json={"parent_id": child["id"]},
    )
    assert response.status_code == 409


def test_delete_department_cascade(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    child = client.post(
        "/departments/",
        json={"name": "Engineering", "parent_id": root["id"]},
    ).json()
    client.post(
        f"/departments/{child['id']}/employees/",
        json={"full_name": "Bob", "position": "Manager"},
    )

    delete_response = client.delete(f"/departments/{child['id']}", params={"mode": "cascade"})
    assert delete_response.status_code == 204
    assert client.get(f"/departments/{child['id']}").status_code == 404


def test_delete_department_reassign(client) -> None:
    root = client.post("/departments/", json={"name": "HQ"}).json()
    old_dept = client.post(
        "/departments/",
        json={"name": "Sales", "parent_id": root["id"]},
    ).json()
    new_dept = client.post(
        "/departments/",
        json={"name": "Marketing", "parent_id": root["id"]},
    ).json()
    employee = client.post(
        f"/departments/{old_dept['id']}/employees/",
        json={"full_name": "Carol", "position": "Seller"},
    ).json()

    response = client.delete(
        f"/departments/{old_dept['id']}",
        params={"mode": "reassign", "reassign_to_department_id": new_dept["id"]},
    )
    assert response.status_code == 204

    detail = client.get(f"/departments/{new_dept['id']}").json()
    assert len(detail["employees"]) == 1
    assert detail["employees"][0]["id"] == employee["id"]


def test_create_employee_in_missing_department_returns_404(client) -> None:
    response = client.post(
        "/departments/9999/employees/",
        json={"full_name": "Ghost", "position": "None"},
    )
    assert response.status_code == 404
