import importlib.abc
import importlib.util

# Monkey-patch: add find_module to FileFinder for backwards compatibility
if not hasattr(importlib.machinery.FileFinder, "find_module"):
    def find_module(self, fullname, path=None):
        try:
            spec = self.find_spec(fullname, path)
            if spec is None:
                return None
            loader = spec.loader
            if loader is None:
                return None
            return loader
        except Exception:
            return None
    importlib.machinery.FileFinder.find_module = find_module
