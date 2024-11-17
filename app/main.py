from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple
from collections import deque

# Pydantic (type checking) Models
class WaterJugRequest(BaseModel):
    x_capacity: int = Field(..., gt=0, description="Capacity of bucket X (must be positive), greater than 0")
    y_capacity: int = Field(..., gt=0, description="Capacity of bucket Y (must be positive), greater than 0")
    z_amount_wanted: int = Field(..., gt=0, description="Target amount of water (must be positive), greater than 0")

    class Config:
        json_schema_extra = {
            "example": {
                "x_capacity": 4,
                "y_capacity": 3,
                "z_amount_wanted": 2
            }
        }

class Step(BaseModel):
    step: int
    bucketX: int
    bucketY: int
    action: str
    status: Optional[str] = None

class WaterJugResponse(BaseModel):
    solution: List[Step]

# In-memory "cache" for previously solved values
MAX_CACHE_SIZE = 10000
solution_cache: Dict[Tuple[int, int, int], List[Step]] = {}
cache_size = 0  # Track cache size to prevent memory leak

def solve_water_jug(x_capacity: int, y_capacity: int, target: int) -> List[Step]:
    global cache_size
    
    # Clear cache if it gets too big
    if cache_size >= MAX_CACHE_SIZE:
        solution_cache.clear()
        cache_size = 0
    
    # Check cache
    cache_key = (x_capacity, y_capacity, target)
    if cache_key in solution_cache:
        return solution_cache[cache_key]
    
    # Early validation
    if target > max(x_capacity, y_capacity):
        solution_cache[cache_key] = [] #Populate cache value even if invalid
        cache_size += 1
        return []

    queue = deque([(0, 0, [])])  # (x, y, steps)
    visited = {(0, 0)}

    while queue:
        x, y, steps = queue.popleft()

        if x == target or y == target:
            # Skip the initial (0,0) state to avoid adding 1 unnecessary step (It is also performed within PDF requirements file)
            solution = format_steps([(x, y, action, is_final) for x, y, action, is_final in steps[1:] + [(x, y, "Target reached", True)]])
            solution_cache[cache_key] = solution
            cache_size += 1
            return solution
        
        next_states = [
            (x_capacity, y, "Fill bucket x"),
            (x, y_capacity, "Fill bucket y"),
            (0, y, "Empty bucket x"),
            (x, 0, "Empty bucket y"),
            (max(0, x - (y_capacity - y)), min(y_capacity, y + x), 
             "Transfer from bucket x to bucket y"),
            (min(x_capacity, x + y), max(0, y - (x_capacity - x)),
             "Transfer from bucket y to bucket x")
        ] #These are all of the possible actions to perform / print

        for new_x, new_y, action in next_states:
            if (new_x, new_y) not in visited:
                visited.add((new_x, new_y))
                queue.append((new_x, new_y, steps + [(x, y, action, False)]))

    solution_cache[cache_key] = []
    cache_size += 1
    return []

def format_steps(steps) -> List[Step]:
    '''Formats the response into easily readable form'''
    return [
        Step(
            step=i + 1,
            bucketX=x,
            bucketY=y,
            action=action,
            status="Solved" if is_final else None
        )
        for i, (x, y, action, is_final) in enumerate(steps)
    ]

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
router = APIRouter(prefix="/api")

@router.post("/solve", response_model=WaterJugResponse)
async def solve_water_jug_route(request: WaterJugRequest):
    try:
        solution = solve_water_jug(request.x_capacity, request.y_capacity, request.z_amount_wanted)
        
        if not solution:
            raise HTTPException(status_code=400, detail="No solution")
        
        return WaterJugResponse(solution=solution)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 