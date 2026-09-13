import sys
from pathlib import Path

# Ensure backend root directory is on the Python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.app import create_app

# Vercel and WSGI servers look for the module-level 'app' instance
app = create_app()

if __name__ == "__main__":
    app.run()
