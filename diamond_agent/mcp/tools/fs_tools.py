"""
Filesystem MCP tools with safety sandboxing.
"""

from typing import Dict, Any
import os
from pathlib import Path


class FilesystemTools:
    """Safe filesystem operations within an allowed base directory."""

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()

    def _resolve_safe(self, rel_path: str) -> Path:
        resolved = (self.base_dir / rel_path).resolve()
        if not str(resolved).startswith(str(self.base_dir)):
            raise PermissionError(f"Access outside base directory is forbidden: {rel_path}")
        return resolved

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read content of a file."""
        target = self._resolve_safe(path)
        if not target.exists():
            return {"error": f"File '{path}' does not exist."}
        try:
            content = target.read_text(encoding="utf-8")
            return {"path": path, "content": content, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file."""
        target = self._resolve_safe(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.write_text(content, encoding="utf-8")
            return {"status": "success", "path": path, "bytes_written": len(content.encode("utf-8"))}
        except Exception as e:
            return {"error": str(e)}

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """List files and subdirectories."""
        target = self._resolve_safe(path)
        if not target.is_dir():
            return {"error": f"Path '{path}' is not a directory."}
        entries = []
        for p in target.iterdir():
            entries.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": p.stat().st_size if p.is_file() else 0,
            })
        return {"directory": path, "entries": entries}
