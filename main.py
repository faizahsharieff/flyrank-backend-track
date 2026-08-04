from fastapi import FastAPI,HTTPException, Response, status
from pydantic import BaseModel
from database import get_connection, init_db

app = FastAPI(
    title="Task API",
    description="Week 3 FlyRank Assignment: A CRUD REST API built with FastAPI and PostgreSQL for managing tasks.",
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