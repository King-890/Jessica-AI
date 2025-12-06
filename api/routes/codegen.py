import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _safe_join(*paths: str) -> str:
    target = os.path.abspath(os.path.join(*paths))
    base = os.path.abspath(BASE_DIR)
    if os.path.commonpath([target, base]) != base:
        raise HTTPException(status_code=403, detail="Forbidden path")
    return target


class GenerateRequest(BaseModel):
    type: str  # python_script | flask_app | react_component
    name: str
    output_path: str | None = None


router = APIRouter()


def render_template(t: str, name: str) -> str:
    t = t.lower()
    if t == "python_script":
        return f"def main():\n    print('Hello from {name}')\n\nif __name__ == '__main__':\n    main()\n"
    if t == "flask_app":
        return (
            "from flask import Flask\n"
            "app = Flask(__name__)\n\n"
            "@app.route('/')\n"
            f"def hello():\n    return 'Hello from {name}'\n\n"
            "if __name__ == '__main__':\n    app.run(host='127.0.0.1', port=8000)\n"
        )
    if t == "react_component":
        comp = name.replace(" ", "")
        return (
            f"export default function {comp}() {{\n"
            f"  return (<div>{comp} says hello</div>);\n"
            "}\n"
        )
    raise HTTPException(status_code=400, detail="Unsupported template type")


@router.post("/generate")
def generate(req: GenerateRequest):
    content = render_template(req.type, req.name)
    wrote = None
    if req.output_path:
        target = _safe_join(BASE_DIR, req.output_path)
        parent = os.path.dirname(target)
        os.makedirs(parent, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        wrote = os.path.relpath(target, BASE_DIR)
    return {"content": content, "written": wrote}