from fastapi import FastAPI
from app.ai.llm import echo_runnable

app = FastAPI(
    title="SafeBite AI Service",
    description="AI explanation layer for SafeBite. This service ONLY explains "
                 "decisions made by the deterministic backend — it never decides "
                 "allergen safety, ingredient classification, or food ranking.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "safebite-ai"}


@app.get("/ai-test")
def ai_test():
    result = echo_runnable.invoke("casein")
    return {"input": "casein", "output": result}