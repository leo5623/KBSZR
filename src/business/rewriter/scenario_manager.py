"""行业场景管理器"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class ScenarioTemplate:
    """场景模板"""
    type: str
    prompt: str
    name: str = ""
    description: str = ""


@dataclass
class IndustryConfig:
    """行业配置"""
    id: str
    name: str
    templates: List[ScenarioTemplate]
    default_style: str = "亲切"


class ScenarioManager:
    """行业场景管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化场景管理器

        Args:
            config: 场景配置字典，格式如下：
                {
                    "beauty": {
                        "name": "美妆教程",
                        "templates": [
                            {"type": "种草安利", "prompt": "..."},
                            {"type": "教程分享", "prompt": "..."}
                        ]
                    }
                }
        """
        self._industries: Dict[str, IndustryConfig] = {}
        self._default_industries()

        # 如果提供了额外配置，合并
        if config:
            self._load_from_config(config)

        logger.info(f"ScenarioManager initialized with {len(self._industries)} industries")

    def _default_industries(self):
        """加载默认行业配置"""
        self._industries = {
            "beauty": IndustryConfig(
                id="beauty",
                name="美妆教程",
                default_style="亲切",
                templates=[
                    ScenarioTemplate(
                        type="种草安利",
                        prompt="你是美妆达人，用亲切热情的语气改写以下文案，突出产品卖点和使用效果，让读者产生购买欲望。",
                        name="种草安利",
                        description="适合推荐美妆产品"
                    ),
                    ScenarioTemplate(
                        type="教程分享",
                        prompt="你是美妆专家，用专业但易懂的语言改写以下教程文案，步骤清晰让读者能轻松上手。",
                        name="教程分享",
                        description="适合化妆技巧教程"
                    ),
                    ScenarioTemplate(
                        type="对比测评",
                        prompt="你是客观测评博主，用中性专业的语气改写以下对比测评文案，公平呈现产品优缺点。",
                        name="对比测评",
                        description="适合产品对比分析"
                    )
                ]
            ),
            "knowledge": IndustryConfig(
                id="knowledge",
                name="知识付费",
                default_style="专业",
                templates=[
                    ScenarioTemplate(
                        type="干货分享",
                        prompt="你是知识博主，用权威但通俗易懂的语气改写以下内容，让读者觉得有收获有价值。",
                        name="干货分享",
                        description="适合知识传播"
                    ),
                    ScenarioTemplate(
                        type="课程推广",
                        prompt="你是课程顾问，用有说服力的语气改写以下课程推广文案，突出课程价值和独特之处。",
                        name="课程推广",
                        description="适合课程推广"
                    ),
                    ScenarioTemplate(
                        type="经验分享",
                        prompt="你是过来人，用真诚分享的语气改写以下经验分享文案，让读者感同身受并获得启发。",
                        name="经验分享",
                        description="适合个人经验分享"
                    )
                ]
            ),
            "ecommerce": IndustryConfig(
                id="ecommerce",
                name="电商带货",
                default_style="活泼",
                templates=[
                    ScenarioTemplate(
                        type="产品介绍",
                        prompt="你是专业带货主播，用热情专业的语气改写以下产品介绍文案，突出卖点、优势和性价比。",
                        name="产品介绍",
                        description="适合产品讲解"
                    ),
                    ScenarioTemplate(
                        type="限时优惠",
                        prompt="你是促销专家，用紧迫感的语气改写以下限时优惠文案，强调限时限量，促进行动。",
                        name="限时优惠",
                        description="适合促销活动"
                    ),
                    ScenarioTemplate(
                        type="开箱分享",
                        prompt="你是种草达人，用兴奋期待的语气改写以下开箱分享文案，让读者感受开箱的乐趣。",
                        name="开箱分享",
                        description="适合开箱视频"
                    )
                ]
            ),
            "food": IndustryConfig(
                id="food",
                name="美食餐饮",
                default_style="活泼",
                templates=[
                    ScenarioTemplate(
                        type="美食推荐",
                        prompt="你是美食博主，用诱人的语言改写以下美食推荐文案，让读者垂涎欲滴。",
                        name="美食推荐",
                        description="适合餐厅/食品推荐"
                    ),
                    ScenarioTemplate(
                        type="食谱分享",
                        prompt="你是烹饪达人，用清晰易懂的步骤改写以下食谱文案，确保读者能轻松复刻。",
                        name="食谱分享",
                        description="适合食谱教程"
                    )
                ]
            ),
            "education": IndustryConfig(
                id="education",
                name="教育培训",
                default_style="专业",
                templates=[
                    ScenarioTemplate(
                        type="学习方法",
                        prompt="你是学习导师，用鼓励的语气改写以下学习方法文案，帮助读者提升学习效率。",
                        name="学习方法",
                        description="适合学习技巧分享"
                    ),
                    ScenarioTemplate(
                        type="教育培训",
                        prompt="你是教育专家，用专业权威的语气改写以下教育培训文案，突出教育价值和效果。",
                        name="教育培训",
                        description="适合教育机构推广"
                    )
                ]
            )
        }

    def _load_from_config(self, config: Dict[str, Any]):
        """从配置加载行业"""
        for industry_id, industry_data in config.items():
            templates = []
            for tpl in industry_data.get("templates", []):
                templates.append(ScenarioTemplate(
                    type=tpl.get("type", ""),
                    prompt=tpl.get("prompt", ""),
                    name=tpl.get("name", ""),
                    description=tpl.get("description", "")
                ))

            self._industries[industry_id] = IndustryConfig(
                id=industry_id,
                name=industry_data.get("name", industry_id),
                default_style=industry_data.get("default_style", "亲切"),
                templates=templates
            )

    def list_industries(self) -> List[Dict[str, str]]:
        """列出所有行业"""
        return [
            {"id": ind.id, "name": ind.name}
            for ind in self._industries.values()
        ]

    def list_scenarios(self, industry_id: str) -> List[Dict[str, str]]:
        """列出某个行业下的所有场景"""
        industry = self._industries.get(industry_id)
        if not industry:
            return []
        return [
            {"type": tpl.type, "name": tpl.name, "description": tpl.description}
            for tpl in industry.templates
        ]

    def get_template(self, industry_id: str, scenario_type: str) -> Optional[ScenarioTemplate]:
        """获取指定行业和场景的模板"""
        industry = self._industries.get(industry_id)
        if not industry:
            return None

        for tpl in industry.templates:
            if tpl.type == scenario_type:
                return tpl

        return None

    def get_prompt(
        self,
        industry_id: Optional[str] = None,
        scenario_type: Optional[str] = None
    ) -> str:
        """
        获取提示词

        Args:
            industry_id: 行业ID（如"beauty"、"knowledge"）
            scenario_type: 场景类型（如"种草安利"）

        Returns:
            提示词文本
        """
        if not industry_id:
            return "你是一位专业的内容创作者，改写以下文案使其更吸引人。"

        industry = self._industries.get(industry_id)
        if not industry:
            return "你是一位专业的内容创作者，改写以下文案使其更吸引人。"

        if not scenario_type:
            # 返回行业默认提示
            if industry.templates:
                return industry.templates[0].prompt
            return "你是一位专业的内容创作者，改写以下文案使其更吸引人。"

        # 查找指定场景
        for tpl in industry.templates:
            if tpl.type == scenario_type:
                return tpl.prompt

        # 没找到，返回默认
        return industry.templates[0].prompt if industry.templates else "你是一位专业的内容创作者，改写以下文案使其更吸引人。"

    def get_default_style(self, industry_id: str) -> str:
        """获取行业的默认风格"""
        industry = self._industries.get(industry_id)
        return industry.default_style if industry else "亲切"


# 全局实例
_scenario_manager: Optional[ScenarioManager] = None


def get_scenario_manager(config: Optional[Dict[str, Any]] = None) -> ScenarioManager:
    """获取场景管理器实例"""
    global _scenario_manager
    if _scenario_manager is None:
        _scenario_manager = ScenarioManager(config)
    return _scenario_manager