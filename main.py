from fastapi import FastAPI,HTTPException, Response, status, Request
from pydantic import BaseModel
from database import get_connection, init_db
from database import supabase  # Import the Supabase client

app = FastAPI(
    title="Task API",
    description="Week 3 FlyRank Assignment: A CRUD REST API built with FastAPI and PostgreSQL for managing tasks.",
)

@app.on_event("startup")
def startup():
    init_db()

class AuthRequest(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: str
    done: bool

@app.get("/")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/tasks")
def get_tasks():

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, done FROM tasks"
        )
        rows = cur.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "title": row[1],
            "done": row[2]
        }
        for row in rows
    ]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, title, done FROM tasks WHERE id = %s",
            (task_id,)
        )

        row = cur.fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }

@app.get("/protected/profile")
def protected_profile(request: Request):
    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    token = authorization[7:].strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail={"error": "Access token required"}
        )

    return {
        "message": "Token received"
    }

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO tasks(title, done)
            VALUES (%s, %s)
            RETURNING id, title, done
            """,
            (task.title, False)
        )

        row = cur.fetchone()

    conn.commit()
    conn.close()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):
    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "user": response.user.model_dump() if response.user else None
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail={"error": "Signup failed"}
        )

@app.post("/auth/login")
def login(data: AuthRequest):
    if not data.email or not data.password:
        raise HTTPException(
            status_code=400,
            detail={"error": "Email and password are required"}
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not response.session:
            raise HTTPException(
                status_code=401,
                detail={"error": "Invalid login credentials"}
            )

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid login credentials"}
        )
    
@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_task: TaskUpdate):

    conn = get_connection()

    with conn.cursor() as cur:

        cur.execute(
            """
            UPDATE tasks
            SET title = %s, done = %s
            WHERE id = %s
            RETURNING id, title, done
            """,
            (
                updated_task.title,
                updated_task.done,
                task_id
            )
        )

        row = cur.fetchone()

    conn.commit()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2]
    }

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM tasks
            WHERE id = %s
            RETURNING id
            """,
            (task_id,)
        )

        row = cur.fetchone()

    conn.commit()
    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)