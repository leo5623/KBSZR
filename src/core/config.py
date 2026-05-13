"""配置加载模块"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置管理器"""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)

        self._config: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        """加载所有配置文件"""
        # 主配置
        config_path = self.config_dir / "config.yaml"
        if config_path.exists():
            self._config = self._load_yaml(config_path)

        # 账号配置
        accounts_path = self.config_dir / "accounts.json"
        if accounts_path.exists():
            with open(accounts_path, "r", encoding="utf-8") as f:
                self._config["accounts"] = json.load(f)

        # 素材库配置
        library_path = self.config_dir / "library.json"
        if library_path.exists():
            with open(library_path, "r", encoding="utf-8") as f:
                self._config["library"] = json.load(f)

        # 文案模板
        templates_path = self.config_dir / "copy_templates.json"
        if templates_path.exists():
            with open(templates_path, "r", encoding="utf-8") as f:
                self._config["copy_templates"] = json.load(f)

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """加载YAML配置"""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的键"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def get_env(self, key: str, default: str = "") -> str:
        """获取环境变量，自动替换${VAR}格式"""
        value = os.getenv(key, default)
        return value

    @property
    def modules(self) -> Dict[str, Any]:
        return self._config.get("modules", {})

    @property
    def queue(self) -> Dict[str, Any]:
        return self._config.get("queue", {})

    @property
    def local(self) -> Dict[str, Any]:
        return self._config.get("local", {})

    @property
    def cloud(self) -> Dict[str, Any]:
        return self._config.get("cloud", {})

    @property
    def accounts(self) -> Dict[str, Any]:
        return self._config.get("accounts", {})

    @property
    def library(self) -> Dict[str, Any]:
        return self._config.get("library", {})

    @property
    def scenarios(self) -> Dict[str, Any]:
        return self._config.get("scenarios", {})


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config