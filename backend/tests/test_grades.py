def test_save_and_list_grades(client, auth_headers):
  login = client.post("/api/login", json={"username": "2024001", "password": "123456"})
  student = login.json()["user"]

  save = client.post(
    "/api/grades",
    json={
      "user_id": student["id"],
      "question_id": "q1",
      "code": "print(1)",
      "language": "python",
      "overall_score": 88,
      "summary": "不错",
      "deductions": [],
      "class_name": "默认班级",
    },
    headers=auth_headers,
  )
  assert save.status_code == 200
  assert save.json()["success"] is True

  grades = client.get("/api/grades")
  assert grades.status_code == 200
  assert len(grades.json()["grades"]) >= 1


def test_save_draft(client):
  login = client.post("/api/login", json={"username": "2024001", "password": "123456"})
  token = login.json()["token"]
  headers = {"Authorization": f"Bearer {token}"}

  save = client.put(
    "/api/drafts",
    json={"question_id": "q1", "code": "x = 1", "language": "python"},
    headers=headers,
  )
  assert save.status_code == 200

  draft = client.get("/api/drafts/q1", headers=headers)
  assert draft.status_code == 200
  assert draft.json()["draft"]["code"] == "x = 1"
