from fastapi import FastAPI,HTTPException, Response, status
from pydantic import BaseModel
from database import get_connection, init_db

app = FastAPI(
    title="Task API",
    description="Week 2 FlyRank Assignment: A simple CRUD API to manage tasks",
)

@app.on_event("startup")
def startup():
    init_db()

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
def get_tasks(
    done: bool | None = None,
    title: str | None = None
):

    conn = get_connection()

    query = "SELECT * FROM tasks"
    params = []

    conditions = []

    if done is not None:
        conditions.append("done = ?")
        params.append(int(done))

    if title:
        conditions.append("title LIKE ?")
        params.append(f"%{title}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    rows = conn.execute(query, params).fetchall()

    conn.close()

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "done": bool(row["done"])
        }
        for row in rows
    ]

@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }