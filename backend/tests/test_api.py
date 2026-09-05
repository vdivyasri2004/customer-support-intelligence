import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password

# Use SQLite for tests (in-memory)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite://"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    response = client.post("/api/auth/register", json={"email": "test@test.com", "password": "TestPass123!"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    def test_register(self, client):
        response = client.post("/api/auth/register", json={"email": "new@test.com", "password": "Password123!"})
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@test.com"

    def test_register_duplicate(self, client):
        client.post("/api/auth/register", json={"email": "dup@test.com", "password": "Password123!"})
        response = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "Password123!"})
        assert response.status_code == 400

    def test_register_short_password(self, client):
        response = client.post("/api/auth/register", json={"email": "short@test.com", "password": "123"})
        assert response.status_code == 422

    def test_login_success(self, client):
        client.post("/api/auth/register", json={"email": "login@test.com", "password": "Password123!"})
        response = client.post("/api/auth/login", json={"email": "login@test.com", "password": "Password123!"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={"email": "wrong@test.com", "password": "Password123!"})
        response = client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "WrongPassword!"})
        assert response.status_code == 401

    def test_me_authenticated(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == "test@test.com"

    def test_me_unauthenticated(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestDatasets:
    def test_list_datasets_empty(self, client, auth_headers):
        response = client.get("/api/datasets", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_load_sample_dataset(self, client, auth_headers):
        response = client.post("/api/datasets/sample", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["rows_processed"] > 0
        assert data["dataset"]["name"] == "Sample Support Tickets"

    def test_list_datasets_after_sample(self, client, auth_headers):
        client.post("/api/datasets/sample", headers=auth_headers)
        response = client.get("/api/datasets", headers=auth_headers)
        assert response.json()["total"] == 1

    def test_get_dataset(self, client, auth_headers):
        create_resp = client.post("/api/datasets/sample", headers=auth_headers)
        dataset_id = create_resp.json()["dataset"]["id"]
        response = client.get(f"/api/datasets/{dataset_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["row_count"] > 0

    def test_delete_dataset(self, client, auth_headers):
        create_resp = client.post("/api/datasets/sample", headers=auth_headers)
        dataset_id = create_resp.json()["dataset"]["id"]
        response = client.delete(f"/api/datasets/{dataset_id}", headers=auth_headers)
        assert response.status_code == 204
        list_resp = client.get("/api/datasets", headers=auth_headers)
        assert list_resp.json()["total"] == 0

    def test_unauthorized_dataset_access(self, client, auth_headers):
        create_resp = client.post("/api/datasets/sample", headers=auth_headers)
        dataset_id = create_resp.json()["dataset"]["id"]
        # Register second user
        client.post("/api/auth/register", json={"email": "other@test.com", "password": "Password123!"})
        other_resp = client.post("/api/auth/login", json={"email": "other@test.com", "password": "Password123!"})
        other_headers = {"Authorization": f"Bearer {other_resp.json()['access_token']}"}
        response = client.get(f"/api/datasets/{dataset_id}", headers=other_headers)
        assert response.status_code == 404

    def test_upload_csv(self, client, auth_headers):
        csv_content = b"ticket_id,subject,description,category,priority,status,channel,agent\nTKT-001,Test Subject,Test description here,Billing,Medium,Open,Email,Agent1\nTKT-002,Another Subject,Another description here,Technical Issue,High,In Progress,Chat,Agent2\nTKT-003,Third Subject,Third description here,Shipping,Low,Resolved,Phone,Agent3\n"
        response = client.post("/api/datasets/upload", headers=auth_headers, files={"file": ("test.csv", csv_content, "text/csv")})
        assert response.status_code == 201
        assert response.json()["rows_processed"] == 3

    def test_upload_invalid_csv(self, client, auth_headers):
        response = client.post("/api/datasets/upload", headers=auth_headers, files={"file": ("test.txt", b"not a csv", "text/plain")})
        assert response.status_code == 400

    def test_upload_empty_csv(self, client, auth_headers):
        response = client.post("/api/datasets/upload", headers=auth_headers, files={"file": ("empty.csv", b"", "text/csv")})
        assert response.status_code == 400


class TestAnalytics:
    def _create_dataset(self, client, auth_headers):
        resp = client.post("/api/datasets/sample", headers=auth_headers)
        return resp.json()["dataset"]["id"]

    def test_get_analytics(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/analytics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["kpis"]["total_tickets"] == 400
        assert len(data["tickets_over_time"]) > 0
        assert len(data["tickets_by_category"]) > 0

    def test_get_analytics_with_filters(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/analytics?category=Billing", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["kpis"]["total_tickets"] > 0

    def test_get_filter_options(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/analytics/filters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["categories"]) > 0
        assert len(data["agents"]) > 0


class TestTickets:
    def _create_dataset(self, client, auth_headers):
        resp = client.post("/api/datasets/sample", headers=auth_headers)
        return resp.json()["dataset"]["id"]

    def test_list_tickets(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/tickets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 400
        assert len(data["tickets"]) <= 20

    def test_list_tickets_pagination(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/tickets?page=1&page_size=10", headers=auth_headers)
        data = response.json()
        assert len(data["tickets"]) == 10
        assert data["page"] == 1

    def test_list_tickets_search(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        response = client.get(f"/api/datasets/{dataset_id}/tickets?search=payment", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] > 0

    def test_get_ticket(self, client, auth_headers):
        dataset_id = self._create_dataset(client, auth_headers)
        list_resp = client.get(f"/api/datasets/{dataset_id}/tickets", headers=auth_headers)
        ticket_id = list_resp.json()["tickets"][0]["id"]
        response = client.get(f"/api/tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["subject"] is not None


class TestML:
    def test_sentiment_analysis(self):
        from app.ml.sentiment import analyze_sentiment
        pos = analyze_sentiment("This is great! I love it!")
        assert pos.sentiment == "Positive"
        neg = analyze_sentiment("This is terrible, worst experience ever")
        assert neg.sentiment == "Negative"
        neut = analyze_sentiment("I need help with my account")
        assert neut.sentiment == "Neutral"

    def test_ticket_classification(self):
        from app.ml.classifier import classify_ticket
        result = classify_ticket("Cannot login to my account", "Password reset not working")
        assert result.category in ["Login", "Account Access"]
        assert result.confidence > 0

    def test_common_issues_detection(self):
        from app.ml.common_issues import detect_common_issues
        from app.models.ticket import Ticket
        from app.models.dataset import Dataset
        from app.models.user import User
        from app.core.security import hash_password
        db = TestingSessionLocal()
        try:
            user = User(email="ml@test.com", password_hash=hash_password("Password123!"))
            db.add(user)
            db.flush()
            dataset = Dataset(user_id=user.id, name="test", source_type="sample", row_count=5)
            db.add(dataset)
            db.flush()
            for i in range(5):
                ticket = Ticket(
                    dataset_id=dataset.id,
                    subject="Payment failed during checkout",
                    description="Payment not processing",
                    category="Payment",
                    priority="High",
                    status="Open",
                )
                db.add(ticket)
            db.commit()
            issues = detect_common_issues(db, dataset.id)
            assert len(issues) > 0
            assert issues[0].frequency >= 3
        finally:
            db.close()
