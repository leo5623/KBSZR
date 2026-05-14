"""配置模块测试"""
import pytest
from pathlib import Path
from src.core.config import Config, get_config


class TestConfig:
    """Config类测试"""

    def test_config_init_default_path(self, tmp_path):
        """测试默认路径初始化"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = Config(config_dir=str(config_dir))
        assert config.config_dir == config_dir

    def test_load_yaml(self, tmp_path):
        """测试YAML加载"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        yaml_file = config_dir / "config.yaml"
        yaml_file.write_text("""
modules:
  rewriter:
    mode: "cloud"
queue:
  max_concurrency: 10
""", encoding="utf-8")

        config = Config(config_dir=str(config_dir))
        assert config.get("modules.rewriter.mode") == "cloud"
        assert config.get("queue.max_concurrency") == 10

    def test_load_json_accounts(self, tmp_path):
        """测试账号配置加载"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        accounts_file = config_dir / "accounts.json"
        accounts_file.write_text('{"douyin": {"cookies": "test"}}', encoding="utf-8")

        config = Config(config_dir=str(config_dir))
        assert config.accounts == {"douyin": {"cookies": "test"}}

    def test_get_with_dot_notation(self, tmp_path):
        """测试点号分隔的键获取"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        yaml_file = config_dir / "config.yaml"
        yaml_file.write_text("""
a:
  b:
    c:
      d: "value"
""", encoding="utf-8")

        config = Config(config_dir=str(config_dir))
        assert config.get("a.b.c.d") == "value"

    def test_get_with_default(self, tmp_path):
        """测试默认值返回"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = Config(config_dir=str(config_dir))
        assert config.get("nonexistent.key", "default") == "default"

    def test_get_env(self, tmp_path, monkeypatch):
        """测试环境变量获取"""
        monkeypatch.setenv("TEST_VAR", "test_value")

        config_dir = tmp_path / "config"
        config_dir.mkdir()

        config = Config(config_dir=str(config_dir))
        assert config.get_env("TEST_VAR") == "test_value"

    def test_properties(self, tmp_path):
        """测试属性访问器"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        yaml_file = config_dir / "config.yaml"
        yaml_file.write_text("""
modules:
  rewriter:
    mode: "local"
queue:
  max_concurrency: 5
local:
  ffmpeg:
    path: "ffmpeg"
cloud:
  rewriter:
    provider: "tongyi"
accounts:
  douyin: {}
library: {}
scenarios: {}
""", encoding="utf-8")

        config = Config(config_dir=str(config_dir))
        assert config.modules == {"rewriter": {"mode": "local"}}
        assert config.queue == {"max_concurrency": 5}
        assert config.local == {"ffmpeg": {"path": "ffmpeg"}}
        assert config.cloud == {"rewriter": {"provider": "tongyi"}}
        assert config.accounts == {"douyin": {}}
        assert config.library == {}
        assert config.scenarios == {}


class TestGetConfig:
    """get_config单例测试"""

    def test_get_config_returns_same_instance(self):
        """测试get_config返回相同实例"""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2