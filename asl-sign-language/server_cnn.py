"""Compatibility entrypoint for the MVC Flask ASL demo.

Use `python run.py` for the primary entrypoint. `python server_cnn.py` remains
supported because earlier setup instructions used this filename.
"""

from run import run_server


if __name__ == "__main__":
    run_server()
