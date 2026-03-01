import os
import tempfile
import shutil

class TempFileManager:
    def __init__(self):
        # Base temp dir for our app
        self.base_dir = os.path.join(tempfile.gettempdir(), "online_compiler_sessions")
        os.makedirs(self.base_dir, exist_ok=True)

    def create_session_dir(self):
        """Creates a unique directory for a compilation session."""
        return tempfile.mkdtemp(dir=self.base_dir)

    def cleanup(self, path):
        """Safely removes a directory or file."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except Exception as e:
            print(f"Error cleaning up {path}: {e}")

temp_manager = TempFileManager()
