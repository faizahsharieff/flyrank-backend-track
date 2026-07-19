from fastapi import FastAPI,HTTPException, status
from pydantic import BaseModel

app = FastAPI()

tasks = [
    {"id": 1, "title": "Study FastAPI", "done": False},
    {"id": 2, "title": "Complete Assignment", "done": False},
    {"id": 3, "title": "Push to GitHub", "done": True}
]

class TaskCreate(BaseModel):
    title: str


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
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):

    for task in tasks:
        if task["id"] == task_id:
            return task

    raise HTTPException(
        status_code=404,
        detail=f"Task {task_id} not found"
    )

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):

    if task.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty"
        )

    new_task = {
        "id": len(tasks) + 1,
        "title": task.title,
        "done": False
    }

    tasks.append(new_task)

    return new_task