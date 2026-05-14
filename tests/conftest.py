"""pytest配置文件"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# pytest配置
def pytest_configure(config):
    """pytest全局配置"""
    config.addinivalue_line("markers", "asyncio: mark test as an asyncio test")
    config.addinivalue_line("markers", "slow: mark test as slow running")