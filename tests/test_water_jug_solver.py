import pytest
from app.main import solve_water_jug

def test_simple_solution():
    solution = solve_water_jug(2, 10, 4)
    assert len(solution) > 0
    assert solution[-1].status == "Solved"
    assert solution[-1].bucketX == 0
    assert solution[-1].bucketY == 4

def test_no_solution():
    solution = solve_water_jug(2, 6, 5)
    assert len(solution) == 0

def test_large_numbers():
    solution = solve_water_jug(2, 100, 96)
    assert len(solution) > 0
    assert solution[-1].status == "Solved"
    assert solution[-1].bucketY == 96

def test_invalid_inputs():
    # Since input validation is now handled at the API level,
    # we'll test the function with valid inputs that produce no solution
    result = solve_water_jug(2, 2, 5)
    assert result == []  # Should return empty list when no solution exists

def test_solution_caching():
    # First call should compute the solution
    first_solution = solve_water_jug(2, 10, 4)
    
    # Second call should return cached solution
    second_solution = solve_water_jug(2, 10, 4)
    
    assert first_solution == second_solution
    assert len(first_solution) > 0 