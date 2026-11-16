import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, enable_foreign_keys, get_db
from main import app
from models import Student


class CollegeAPITest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        from sqlalchemy import event

        event.listen(self.engine, "connect", enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

        def override_db():
            with self.session_factory() as session:
                yield session

        self.addCleanup(self.engine.dispose)
        self.addCleanup(app.dependency_overrides.clear)
        app.dependency_overrides[get_db] = override_db
        self.enterContext(patch("main.engine", self.engine))
        self.client = self.enterContext(TestClient(app))

    def test_complete_workflow(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in ("/api/departments/", "/api/students/"):
            self.assertEqual(set(paths[path]), {"get", "post"})
            self.assertIn("201", paths[path]["post"]["responses"])
            self.assertEqual(self.client.get(path).json(), [])

        departments = []
        for department_id, name in enumerate(("Computer Science", "Mechanical Engineering"), 1):
            expected = {"department_id": department_id, "department_name": name}
            response = self.client.post("/api/departments/", json={"department_name": name})
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json(), expected)
            departments.append(expected)
        self.assertEqual(self.client.get("/api/departments/").json(), departments)

        students = []
        for department_id, name in enumerate(("Asha Rao", "Rahul Mehta"), 1):
            payload = {"student_name": name, "department_id": department_id}
            response = self.client.post("/api/students/", json=payload)
            expected = dict(payload, student_id=department_id,
                            department_name=departments[department_id - 1]["department_name"])
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json(), expected)
            students.append(expected)
        self.assertEqual(self.client.get("/api/students/").json(), students)

        response = self.client.post(
            "/api/students/", json={"student_name": "Ram", "department_id": 10}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "Department not found"})
        self.assertEqual(self.client.get("/api/students/").json(), students)

    def test_invalid_inputs(self):
        for name in ("", "   ", "x" * 101):
            self.assertEqual(self.client.post(
                "/api/departments/", json={"department_name": name}
            ).status_code, 422)
            self.assertEqual(self.client.post(
                "/api/students/", json={"student_name": name, "department_id": 1}
            ).status_code, 422)
        self.assertEqual(self.client.post(
            "/api/students/", json={"student_name": "Asha", "department_id": 0}
        ).status_code, 422)

    def test_database_enforces_foreign_key(self):
        with self.session_factory() as session:
            session.add(Student(student_name="Orphan", department_id=10))
            with self.assertRaises(IntegrityError):
                session.commit()
            session.rollback()
            self.assertEqual(session.scalars(select(Student)).all(), [])

    def test_get_db_closes_session(self):
        with patch("database.SessionLocal") as session_factory:
            dependency = get_db()
            self.assertIs(next(dependency), session_factory.return_value.__enter__.return_value)
            dependency.close()
            session_factory.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()