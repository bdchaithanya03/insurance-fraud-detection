from backend.app import app
from backend.db import init_database


if __name__ == "__main__":
    init_database()
    app.run(debug=True)
