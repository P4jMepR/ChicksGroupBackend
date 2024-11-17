
# Water Jug Problem Solver API

This API, built with FastAPI, provides a solution to the classic *Water Jug Problem*, where the objective is to measure a specific amount of water using only two jugs of given capacities. The solution details each step required to achieve the target measurement using actions like filling, emptying, and transferring water between the two jugs.

---

## Features

- **Endpoint to solve the Water Jug Problem** with detailed steps and actions
- **CORS-enabled** for cross-origin requests, making it easy to use in different front-end environments
- **In-memory cache** for previously solved problems to improve response times

---

## Setup and Installation

### Prerequisites
- Python 3.7 or later
- FastAPI, Pydantic, and Uvicorn packages

### Install Dependencies
To install the necessary packages, run within main directory:

### General usage
Code was tested in Windows 10 environment. Adjust all terminal commands accordingly to the provided example basing on system at use.
```bash
Windows: python -m pip install -r requirements.txt
UNIX: python3 -m pip install -r requirements.txt
```

### Run the API
To start the API:
```bash
cd app
python main.py
```
This will start the server on `http://127.0.0.1:8000` unless port is already used.

---

## API Usage

### Endpoint

**POST** `/api/solve`

**Description:** Solves the Water Jug Problem for given jug capacities and target amount.

#### Request Body (JSON)
- **`x_capacity`** (int): Capacity of the first jug (must be a positive integer).
- **`y_capacity`** (int): Capacity of the second jug (must be a positive integer).
- **`z_amount_wanted`** (int): Target amount of water to be measured (must be a positive integer).

#### Example Request
```json
{
    "x_capacity": 3,
    "y_capacity": 5,
    "z_amount_wanted": 4
}
```

#### Response Body (JSON)
- **`solution`**: A list of steps detailing the actions taken to reach the target amount, including:
  - **`step`** (int): Step number in the solution sequence
  - **`bucketX`** (int): Amount of water in the first jug after this step
  - **`bucketY`** (int): Amount of water in the second jug after this step
  - **`action`** (str): Description of the action taken in this step
  - **`status`** (str, optional): "Solved" if this is the final step in the solution

#### Example Response
```json
{
    "solution": [
        {"step": 1, "bucketX": 3, "bucketY": 0, "action": "Fill bucket x"},
        {"step": 2, "bucketX": 0, "bucketY": 3, "action": "Transfer from bucket x to bucket y"},
        {"step": 3, "bucketX": 3, "bucketY": 3, "action": "Fill bucket x"},
        {"step": 4, "bucketX": 1, "bucketY": 5, "action": "Transfer from bucket x to bucket y"},
        {"step": 5, "bucketX": 1, "bucketY": 0, "action": "Empty bucket y"},
        {"step": 6, "bucketX": 0, "bucketY": 1, "action": "Transfer from bucket x to bucket y"},
        {"step": 7, "bucketX": 3, "bucketY": 1, "action": "Fill bucket x"},
        {"step": 8, "bucketX": 0, "bucketY": 4, "action": "Transfer from bucket x to bucket y", "status": "Solved"}
    ]
}
```

#### Error Responses
- **400**: No solution exists or invalid inputs provided.

---

## Project Structure

- `main.py`: The primary file that contains the API logic, request/response models, and the water jug problem-solving algorithm.

---

## Cache for Efficiency

The solution cache stores previously computed solutions in memory to speed up repeated requests for the same jug capacities and target.

---

## Notes

- Ensure input values are positive integers, as negative or zero values will result in an error.
- If the target amount is larger than the capacities of both jugs, the API returns a message indicating that no solution exists.

---
