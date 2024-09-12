## Backend Setup

1. Open a new terminal, activate the virtual environment, and navigate to the backend directory:
   ```bash
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   cd backend
   ```
2. Set up the OpenAI API Key:
- Go to: https://platform.openai.com/api-keys
- Login or signup, select "Create new secret key", name it, and copy it
- Export the environment variable:
  ``` bash
  export OPEN_API_KEY=xyz
  ```
3. Install Poetry:
- Make sure you're in the `/backend` folder
- For macOS:
  ```
  brew install poetry
  ```
- For Linux, macOS, Windows (WSL):
  ```
  curl -sSL https://install.python-poetry.org | python3 -
  ```
- Check installation:
  ```
  poetry --version
  ```

4. Install dependencies:
  ``` bash
  poetry install
  ```
5. Start the FastAPI server:
  ``` bash
  poetry shell
  uvicorn main:app --reload
  ```

Your local host on port 8000 should now be running the API: http://127.0.0.1:8000/

> Note: If you get an error in the `transcribe_audio.py` file, you might need to upgrade openAI:
> ```
> pip install --upgrade openai
> ```

## Recap
- Next.js frontend is running on http://localhost:3000/
- FastAPI server is running on http://127.0.0.1:8000/

