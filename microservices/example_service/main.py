from fastapi import FastAPI

app = FastAPI(title="ExampleService")

@app.get("/")
async def read_root():
    return {"message": "Hello from ExampleService"}

# Add other endpoints here

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)