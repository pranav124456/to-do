from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

from database import user_collection, task_collection, client
from models import User, Task
from auth import hash_password, verify_password
from schemas import task_helper

# ---------------- CONFIG ----------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTES ----------------

@app.get("/")
def root():
    return {"message": "Backend is running"}

@app.get("/health")
def health():
    try:
        # Test MongoDB connection
        client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/test-auth")
def test_auth():
    try:
        from auth import hash_password, verify_password
        test_pw = "test123"
        hashed = hash_password(test_pw)
        verified = verify_password(test_pw, hashed)
        return {"hash_works": True, "verify_works": verified, "hash_preview": hashed[:30]}
    except Exception as e:
        import traceback
        return {"hash_works": False, "error": str(e), "traceback": traceback.format_exc()}

@app.post("/signup")
def signup(user: User):
    try:
        existing_user = user_collection.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")

        hashed_password = hash_password(user.password)
        result = user_collection.insert_one({
            "email": user.email,
            "password": hashed_password
        })

        return {"message": "Signup successful", "id": str(result.inserted_id)}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Signup error: {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Server error: {error_msg}")

@app.post("/login")
def login(user: User):
    try:
        db_user = user_collection.find_one({"email": user.email})

        if not db_user or not verify_password(user.password, db_user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"message": "Login successful"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.get("/tasks/{email}")
def get_tasks(email: str):
    try:
        tasks = task_collection.find({"user_email": email})
        return [task_helper(task) for task in tasks]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.post("/tasks")
def create_task(task: Task):
    try:
        result = task_collection.insert_one({
            "title": task.title,
            "completed": task.completed,
            "user_email": task.user_email
        })
        return {"id": str(result.inserted_id), "message": "Task created"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.put("/tasks/{task_id}")
def update_task(task_id: str, completed: bool = Query(None), title: str = Query(None)):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    if completed is None and title is None:
        raise HTTPException(status_code=400, detail="At least one field (completed or title) must be provided")
    
    try:
        update_data = {}
        if completed is not None:
            update_data["completed"] = completed
        if title is not None:
            update_data["title"] = title
        
        result = task_collection.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    if not ObjectId.is_valid(task_id):
        raise HTTPException(status_code=400, detail="Invalid task ID")
    
    try:
        result = task_collection.delete_one({"_id": ObjectId(task_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")
