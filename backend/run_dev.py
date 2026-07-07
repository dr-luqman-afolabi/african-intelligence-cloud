"""Local dev entrypoint — chdir's to this file's directory first so the
relative `.env` file (DATABASE_URL, SECRET_KEY, etc.) resolves correctly
regardless of the caller's current working directory."""
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
