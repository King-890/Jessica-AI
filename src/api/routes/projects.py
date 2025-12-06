import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKSPACE_DIR = os.path.join(BASE_DIR, "workspace")


def _safe_join(*paths: str) -> str:
    target = os.path.abspath(os.path.join(*paths))
    base = os.path.abspath(BASE_DIR)
    if os.path.commonpath([target, base]) != base:
        raise HTTPException(status_code=403, detail="Forbidden path")
    return target


class ProjectRequest(BaseModel):
    type: str  # python | flask | react | unity
    name: str


router = APIRouter()


@router.post("/create")
def create_project(req: ProjectRequest):
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    proj_root = _safe_join(WORKSPACE_DIR, req.name)
    if os.path.exists(proj_root):
        raise HTTPException(status_code=409, detail="Project already exists")
    os.makedirs(proj_root, exist_ok=True)

    t = req.type.lower()
    created = []
    if t == "python":
        main_path = os.path.join(proj_root, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write("print('Hello from Python project')\n")
        created.append(main_path)
    elif t == "flask":
        app_path = os.path.join(proj_root, "app.py")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(
                """
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask!'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)
""".strip()
            )
        created.append(app_path)
        with open(os.path.join(proj_root, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("flask\n")
    elif t == "react":
        readme = os.path.join(proj_root, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                """
# React App Scaffold

This is a placeholder project. To initialize a Vite React app:

1. Open a terminal in this folder
2. Run: npm create vite@latest . -- --template react
3. Then: npm install && npm run dev
""".strip()
            )
        created.append(readme)
    elif t == "unity":
        readme = os.path.join(proj_root, "README.md")
        with open(readme, "w", encoding="utf-8") as f:
            f.write(
                """
# Unity Project Scaffold

This is a placeholder folder. Use Unity Hub to create a new project here.
Open Unity Hub, choose 'New project', set this folder as the location.
""".strip()
            )
        created.append(readme)
    else:
        raise HTTPException(status_code=400, detail="Unsupported project type")

    return {"project_root": os.path.relpath(proj_root, BASE_DIR), "created": [os.path.relpath(p, BASE_DIR) for p in created]}