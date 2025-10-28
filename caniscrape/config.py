import json
from pathlib import Path
from typing import Any

class Config:
    CONFIG_DIR = '.caniscrape'
    CONFIG_FILE = 'config'
    DEFAULT_API_ENDPOINT = 'https://caniscrape-web-production.up.railway.app'

    def __init__(self, base_path: str | Path = '.'):
        self.base_path = Path(base_path).resolve()
        self.config_dir = self.base_path / self.CONFIG_DIR
        self.config_file = self.config_dir / self.CONFIG_FILE
        self._data: dict = {}

        if self.config_file.exists():
            self._load()
    
    def _load(self) -> None:
        """
        Load config from disk.
        """
        try:
            with open(self.config_file, 'r') as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[yellow]Warning: Config file corrupted, resetting: {str(e)}[/yellow]")
            self._data = {}
    
    def save(self) -> None:
        self.config_dir.mkdir(exist_ok=True)

        temp_file = self.config_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self._data, f, indent=2)
            temp_file.replace(self.config_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise Exception(f'Failed to save config.')
    
    def is_linked(self) -> bool:
        """
        Check if this directory is linked to a cloud project.
        """
        return 'project_id' in self._data and 'api_token' in self._data
    
    def get(self, key: str, default: Any | None = None) -> Any:
        """
        Get a config value.
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a config value (doesn't save to disk until save() is called).
        """
        self._data[key] = value
    
    def delete(self, key: str) -> None:
        """
        Delete a config value.
        """
        self._data.pop(key, None)

    def clear(self) -> None:
        """
        Clear the config (unlink project).
        """
        self._data = {}
        if self.config_file.exists():
            self.config_file.unlink()
    
    def get_project_id(self) -> str | None:
        """
        Get project ID if linked.
        """
        return self.get('project_id')
    
    def get_api_token(self) -> str | None:
        """
        Get API token if linked.
        """
        return self.get('api_token')
    
    def get_api_endpoint(self) -> str:
        """
        Get API Endpoint (default fallback).
        """
        return self.get('api_endpoint', self.DEFAULT_API_ENDPOINT)
    
def find_config_in_parents() -> Config | None:
    current = Path.cwd()

    for parent in [current] + list(current.parents):
        config = Config(parent)
        if config.is_linked():
            return config
    
    return None