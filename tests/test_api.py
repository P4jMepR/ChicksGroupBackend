from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_solve_endpoint_success():
    response = client.post(
        "/api/solve",
        json={
            "x_capacity": 2,
            "y_capacity": 10,
            "z_amount_wanted": 4
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "solution" in data
    assert len(data["solution"]) > 0
    
    first_step = data["solution"][0]
    assert "step" in first_step
    assert "bucketX" in first_step
    assert "bucketY" in first_step
    assert "action" in first_step
    
    final_step = data["solution"][-1]
    assert final_step["status"] == "Solved"
    assert final_step["bucketX"] == 0
    assert final_step["bucketY"] == 4

def test_solve_endpoint_no_solution():
    response = client.post(
        "/api/solve",
        json={
            "x_capacity": 2,
            "y_capacity": 6,
            "z_amount_wanted": 5
        }
    )
    assert response.status_code == 400
    assert "detail" in response.json()

def test_invalid_input():
    response = client.post(
        "/api/solve",
        json={
            "x_capacity": -1,
            "y_capacity": 6,
            "z_amount_wanted": 5
        }
    )
    assert response.status_code == 422
    assert "greater than 0" in response.json()["detail"][0]["msg"].lower()
    