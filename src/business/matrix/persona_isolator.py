"""多账号人设隔离"""
import json
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from loguru import logger


class PersonaType(Enum):
    """人设类型"""
    BEAUTY = "beauty"           # 美妆博主
    KNOWLEDGE = "knowledge"     # 知识博主
    ECOMMERCE = "ecommerce"     # 带货博主
    LIFE = "life"               # 生活博主
    FITNESS = "fitness"         # 健身博主
    FOOD = "food"              # 美食博主
    MOTHER = "mother"           # 母婴博主
    TRAVEL = "travel"           # 旅游博主


@dataclass
class PersonaConfig:
    """人设配置"""
    persona_id: str
    persona_name: str
    persona_type: PersonaType
    avatar_id: str
    voice_id: str
    background_id: str
    tone_style: str           # 语气风格：亲切/专业/活泼/沉稳
    banned_words: List[str] = field(default_factory=list)   # 禁用词
    preferred_hashtags: List[str] = field(default_factory=list)  # 偏好话题
    platform_bindings: Dict[str, str] = field(default_factory=dict)  # 平台绑定
    description: str = ""


@dataclass
class AccountProfile:
    """账号配置"""
    account_id: str
    platform: str              # douyin/kuaishou/xiaohongshu
    account_name: str
    persona_id: str            # 关联的人设ID
    content_category: str      # 内容分类
    is_active: bool = True
    created_at: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class AccountIsolationResult:
    """隔离结果"""
    success: bool
    differentiated_content: str = ""
    applied_persona: str = ""
    warnings: List[str] = field(default_factory=list)


class PersonaIsolator:
    """
    多账号人设隔离器

    确保多账号内容差异化，避免同质化
    """

    def __init__(self):
        self._personas: Dict[str, PersonaConfig] = {}
        self._accounts: Dict[str, AccountProfile] = {}
        self._load_data()

    def _load_data(self):
        """加载数据"""
        # 加载人设配置
        persona_path = "./data/personas.json"
        if os.path.exists(persona_path):
            try:
                with open(persona_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        persona = PersonaConfig(**item)
                        self._personas[persona.persona_id] = persona
            except Exception as e:
                logger.error(f"加载人设配置失败: {e}")

        # 加载账号配置
        account_path = "./data/accounts_isolated.json"
        if os.path.exists(account_path):
            try:
                with open(account_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        account = AccountProfile(**item)
                        self._accounts[account.account_id] = account
            except Exception as e:
                logger.error(f"加载账号配置失败: {e}")

        logger.info(f"加载 {len(self._personas)} 个人设, {len(self._accounts)} 个账号")

    def _save_data(self):
        """保存数据"""
        os.makedirs("./data", exist_ok=True)

        # 保存人设
        persona_path = "./data/personas.json"
        with open(persona_path, "w", encoding="utf-8") as f:
            data = [vars(p) for p in self._personas.values()]
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 保存账号
        account_path = "./data/accounts_isolated.json"
        with open(account_path, "w", encoding="utf-8") as f:
            data = [vars(a) for a in self._accounts.values()]
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ========== 人设管理 ==========

    def add_persona(self, persona: PersonaConfig) -> bool:
        """添加人设"""
        if persona.persona_id in self._personas:
            logger.warning(f"人设 {persona.persona_id} 已存在")
            return False

        self._personas[persona.persona_id] = persona
        self._save_data()
        logger.info(f"添加人设: {persona.persona_name}")
        return True

    def remove_persona(self, persona_id: str) -> bool:
        """移除人设"""
        if persona_id not in self._personas:
            return False

        del self._personas[persona_id]
        self._save_data()
        return True

    def get_persona(self, persona_id: str) -> Optional[PersonaConfig]:
        """获取人设"""
        return self._personas.get(persona_id)

    def list_personas(self) -> List[PersonaConfig]:
        """列出所有人设"""
        return list(self._personas.values())

    # ========== 账号管理 ==========

    def add_account(self, account: AccountProfile) -> bool:
        """添加账号"""
        if account.account_id in self._accounts:
            logger.warning(f"账号 {account.account_id} 已存在")
            return False

        self._accounts[account.account_id] = account
        self._save_data()
        logger.info(f"添加账号: {account.account_name}")
        return True

    def remove_account(self, account_id: str) -> bool:
        """移除账号"""
        if account_id not in self._accounts:
            return False

        del self._accounts[account_id]
        self._save_data()
        return True

    def get_account(self, account_id: str) -> Optional[AccountProfile]:
        """获取账号"""
        return self._accounts.get(account_id)

    def list_accounts(self, platform: str = None) -> List[AccountProfile]:
        """列出账号"""
        accounts = list(self._accounts.values())
        if platform:
            accounts = [a for a in accounts if a.platform == platform]
        return accounts

    # ========== 内容差异化 ==========

    def differentiate_content(
        self,
        content: str,
        account_id: str
    ) -> AccountIsolationResult:
        """
        内容差异化处理

        Args:
            content: 原始内容
            account_id: 账号ID

        Returns:
            AccountIsolationResult: 差异化结果
        """
        warnings = []

        # 1. 获取账号信息
        account = self._accounts.get(account_id)
        if not account:
            return AccountIsolationResult(
                success=False,
                warnings=["账号不存在"]
            )

        # 2. 获取关联人设
        persona = self._personas.get(account.persona_id)
        if not persona:
            return AccountIsolationResult(
                success=False,
                warnings=["人设不存在"]
            )

        differentiated = content

        # 3. 应用禁用词过滤
        for word in persona.banned_words:
            if word in differentiated:
                differentiated = differentiated.replace(word, "*" * len(word))
                warnings.append(f"已过滤禁用词: {word}")

        # 4. 应用语气风格调整
        differentiated = self._apply_tone_style(differentiated, persona.tone_style)

        # 5. 添加人设偏好话题
        if persona.preferred_hashtags:
            hashtags = " ".join(persona.preferred_hashtags[:2])
            if hashtags:
                differentiated = differentiated + "\n\n" + hashtags

        return AccountIsolationResult(
            success=True,
            differentiated_content=differentiated,
            applied_persona=persona.persona_name,
            warnings=warnings
        )

    def _apply_tone_style(self, content: str, tone: str) -> str:
        """应用语气风格"""
        # 简单实现，实际可用 LLM 更精准
        if tone == "活泼":
            # 添加活泼词汇
            prefixes = ["哈哈", "太棒了", "绝绝子"]
            import random
            if not content.startswith(random.choice(prefixes)):
                content = random.choice(prefixes) + "，" + content

        elif tone == "专业":
            # 添加专业词汇
            if "具体" not in content and "分析" not in content:
                content = "从专业角度来看，" + content

        elif tone == "亲切":
            # 添加亲切词汇
            if "大家" not in content:
                content = "大家好，" + content

        elif tone == "沉稳":
            # 添加沉稳词汇
            if "需要" not in content:
                content = "需要注意的是，" + content

        return content

    def get_persona_statistics(self) -> Dict:
        """获取人设统计"""
        persona_stats = {}
        for persona in self._personas.values():
            linked_accounts = [
                a for a in self._accounts.values()
                if a.persona_id == persona.persona_id
            ]
            persona_stats[persona.persona_id] = {
                "name": persona.persona_name,
                "type": persona.persona_type.value,
                "linked_accounts": len(linked_accounts)
            }
        return persona_stats


# 全局实例
_isolator: Optional[PersonaIsolator] = None


def get_persona_isolator() -> PersonaIsolator:
    """获取隔离器实例"""
    global _isolator
    if _isolator is None:
        _isolator = PersonaIsolator()
    return _isolator