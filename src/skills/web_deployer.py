def handle(prompt: str):
    text = (prompt or "").lower()
    if "deploy website" in text or "web deployer" in text:
        return "Web Deployer skill engaged: deploying site (stub)."
    return None