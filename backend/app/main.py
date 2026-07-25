from fastapi import FastAPI

app = FastAPI(title="Sign Language Learning & Assessment Platform")

@app.get("/")
def root():
    return {"message": "Sign Language Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}