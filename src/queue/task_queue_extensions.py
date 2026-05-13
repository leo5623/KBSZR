"""任务队列扩展 - 新增任务类型和处理器映射"""
from enum import Enum
from typing import Callable, Awaitable, Dict, Any

from loguru import logger

from src.business.post_production.sensitive_filter import SensitiveWordFilter, SensitiveWordResult
from src.business.post_production.text_segmenter import TextSegmenter, SegmentResult
from src.business.content.title_generator import TitleGenerator, TitleResult
from src.business.tts.emotion_mapper import EmotionTTSMapper, TextEmotion, TTSParams
from src.business.audio.bgm_matcher import BGMMatcher, BGMTrack


class TaskType(Enum):
    """任务类型（扩展）"""
    # 原有任务
    TTS = "tts"
    DIGITAL_HUMAN = "digital_human"
    VIDEO_PROCESS = "video_process"
    SUBTITLE = "subtitle"
    AUDIO_PROCESS = "audio_process"
    DISTRIBUTE = "distribute"

    # 新增任务
    SENSITIVE_FILTER = "sensitive_filter"      # 敏感词过滤
    TEXT_SEGMENT = "text_segment"              # 文本分段
    TITLE_GENERATE = "title_generate"         # 标题生成
    EMOTION_ANALYZE = "emotion_analyze"        # 情绪分析
    BGM_MATCH = "bgm_match"                   # BGM 匹配


@dataclass
class TaskHandlerResult:
    """任务处理器结果"""
    success: bool
    data: Any = None
    error: str = ""


from dataclasses import dataclass


class TaskRouter:
    """
    任务路由器

    根据任务类型路由到不同的处理器
    """

    def __init__(self):
        self._handlers: Dict[TaskType, Callable] = {}
        self._init_default_handlers()

    def _init_default_handlers(self):
        """初始化默认处理器（简单实现）"""
        # 敏感词过滤处理器
        async def sensitive_filter_handler(task) -> TaskHandlerResult:
            try:
                text = task.data.get("text", "")
                filter = SensitiveWordFilter()
                result: SensitiveWordResult = await filter.filter(text)
                return TaskHandlerResult(
                    success=result.is_passed,
                    data={
                        "filtered_text": result.filtered_text,
                        "detected_words": result.detected_words,
                        "suggestion": result.suggestion
                    }
                )
            except Exception as e:
                return TaskHandlerResult(success=False, error=str(e))

        # 文本分段处理器
        async def text_segment_handler(task) -> TaskHandlerResult:
            try:
                text = task.data.get("text", "")
                segmenter = TextSegmenter()
                result: SegmentResult = segmenter.segment(text)
                return TaskHandlerResult(
                    success=True,
                    data={
                        "segments": [
                            {
                                "index": s.index,
                                "text": s.text,
                                "duration": s.duration,
                                "emotion": s.emotion.value
                            }
                            for s in result.segments
                        ],
                        "total_duration": result.total_duration
                    }
                )
            except Exception as e:
                return TaskHandlerResult(success=False, error=str(e))

        # 标题生成处理器
        async def title_generate_handler(task) -> TaskHandlerResult:
            try:
                content = task.data.get("content", "")
                category = task.data.get("category")
                generator = TitleGenerator()
                result: TitleResult = await generator.generate(content, category=category)
                return TaskHandlerResult(
                    success=True,
                    data={
                        "title": result.title,
                        "subtitle": result.subtitle,
                        "hashtags": result.hashtags,
                        "platform_adapted": {
                            p.value: v for p, v in result.platform_adapted.items()
                        }
                    }
                )
            except Exception as e:
                return TaskHandlerResult(success=False, error=str(e))

        # 情绪分析处理器
        async def emotion_analyze_handler(task) -> TaskHandlerResult:
            try:
                text = task.data.get("text", "")
                mapper = EmotionTTSMapper()
                emotion, params = mapper.map_emotion_to_tts(text)
                return TaskHandlerResult(
                    success=True,
                    data={
                        "emotion": emotion.value,
                        "tts_params": {
                            "speed": params.speed,
                            "pitch": params.pitch,
                            "volume": params.volume,
                            "voice_id": params.voice_id
                        }
                    }
                )
            except Exception as e:
                return TaskHandlerResult(success=False, error=str(e))

        # BGM 匹配处理器
        async def bgm_match_handler(task) -> TaskHandlerResult:
            try:
                emotion = task.data.get("emotion", "calm")
                duration = task.data.get("duration")
                platform = task.data.get("platform")
                matcher = BGMMatcher()
                result = matcher.match(emotion, duration, platform)
                return TaskHandlerResult(
                    success=result.is_found,
                    data={
                        "bgm": {
                            "id": result.bgm.id if result.bgm else None,
                            "name": result.bgm.name if result.bgm else None,
                            "file_path": result.bgm.file_path if result.bgm else None
                        } if result.bgm else None,
                        "fallback": {
                            "id": result.fallback_bgm.id if result.fallback_bgm else None,
                            "name": result.fallback_bgm.name if result.fallback_bgm else None
                        } if result.fallback_bgm else None
                    }
                )
            except Exception as e:
                return TaskHandlerResult(success=False, error=str(e))

        # 注册处理器
        self._handlers[TaskType.SENSITIVE_FILTER] = sensitive_filter_handler
        self._handlers[TaskType.TEXT_SEGMENT] = text_segment_handler
        self._handlers[TaskType.TITLE_GENERATE] = title_generate_handler
        self._handlers[TaskType.EMOTION_ANALYZE] = emotion_analyze_handler
        self._handlers[TaskType.BGM_MATCH] = bgm_match_handler

        logger.info("Task handlers initialized")

    def register_handler(self, task_type: TaskType, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type.value}")

    async def handle(self, task) -> TaskHandlerResult:
        """处理任务"""
        task_type = task.type

        if task_type not in self._handlers:
            return TaskHandlerResult(
                success=False,
                error=f"No handler for task type: {task_type.value}"
            )

        handler = self._handlers[task_type]
        return await handler(task)

    def get_supported_types(self) -> list:
        """获取支持的任务类型"""
        return [t.value for t in self._handlers.keys()]


# 全局实例
_task_router: TaskRouter = None


def get_task_router() -> TaskRouter:
    """获取任务路由器"""
    global _task_router
    if _task_router is None:
        _task_router = TaskRouter()
    return _task_router


# 便捷函数：创建任务
def create_task(
    task_type: TaskType,
    data: Dict[str, Any],
    max_retries: int = 3
):
    """
    创建任务的便捷函数

    Args:
        task_type: 任务类型
        data: 任务数据
        max_retries: 最大重试次数

    Returns:
        Task: 任务实例
    """
    from src.queue.task_queue import Task
    return Task(
        type=task_type,
        data=data,
        max_retries=max_retries
    )


# 使用示例
"""
from src.queue.task_queue_extensions import TaskType, create_task, get_task_router

# 创建任务
task = create_task(
    TaskType.SENSITIVE_FILTER,
    {"text": "要检测的文案内容"}
)

# 添加到队列
queue = get_queue()
await queue.add_task(task)

# 或者直接使用路由器处理
router = get_task_router()
result = await router.handle(task)
"""