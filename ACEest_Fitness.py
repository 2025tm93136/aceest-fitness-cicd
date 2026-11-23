"""ACEest Fitness & Gym - application entry point (WSGI: ACEest_Fitness:app)."""
import os

from aceest import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))  # nosec B104 - container entrypoint
