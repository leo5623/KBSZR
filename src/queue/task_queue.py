"""分批延时队列 - 核心调度模块"""
import asyncio
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from loguru import logger


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class TaskType(Enum):
    """任务类型"""
    TTS = "tts"
    DIGITAL_HUMAN = "digital_human"
    VIDEO_PROCESS = "video_process"
    SUBTITLE = "subtitle"
    AUDIO_PROCESS = "audio_process"
    DISTRIBUTE = "distribute"


@dataclass
class Task:
    """任务定义"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: TaskType = TaskType.TTS
    status: TaskStatus = TaskStatus.PENDING
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class BatchedDelayQueue:
    """
    分批延时队列
    - 并发数 ≤ max_concurrency
    - 任务间隔 min_interval ~ max_interval 秒（随机）
    - 失败自动重试（最多max_retries次）
    """

    def __init__(
        self,
        max_concurrency: int = 5,
        min_interval: int = 10,
        max_interval: int = 30,
        max_retries: int = 3
    ):
        self.max_concurrency = max_concurrency
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.max_retries = max_retries

        self._queue: asyncio.Queue = asyncio.Queue()
        self._running_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._workers: List[asyncio.Task] = []
        self._is_running = False

        logger.info(f"TaskQueue initialized: max_concurrency={max_concurrency}, "
                   f"interval={min_interval}-{max_interval}s, max_retries={max_retries}")

    async def start(self):
        """启动队列"""
        if self._is_running:
            return

        self._is_running = True
        # 启动worker
        for i in range(self.max_concurrency):
            worker = asyncio.create_task(self._worker(worker_id=i))
            self._workers.append(worker)

        logger.info(f"TaskQueue started with {self.max_concurrency} workers")

    async def stop(self):
        """停止队列"""
        self._is_running = False

        # 取消所有worker
        for worker in self._workers:
            worker.cancel()

        # 等待所有worker结束
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("TaskQueue stopped")

    async def add_task(self, task: Task) -> str:
        """
        添加任务到队列
        返回任务ID
        """
        task.max_retries = self.max_retries
        await self._queue.put(task)
        logger.debug(f"Task {task.id} added to queue, type={task.type.value}")
        return task.id

    async def add_tasks(self, tasks: List[Task]) -> List[str]:
        """批量添加任务"""
        task_ids = []
        for task in tasks:
            task_id = await self.add_task(task)
            task_ids.append(task_id)
        logger.info(f"Added {len(tasks)} tasks to queue")
        return task_ids

    async def _worker(self, worker_id: int):
        """Worker协程"""
        logger.debug(f"Worker {worker_id} started")

        while self._is_running:
            try:
                # 从队列获取任务
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            # 处理任务
            await self._process_task(worker_id, task)
            self._queue.task_done()

        logger.debug(f"Worker {worker_id} stopped")

    async def _process_task(self, worker_id: int, task: Task):
        """处理单个任务"""
        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self._running_tasks[task.id] = task

            logger.info(f"[Worker {worker_id}] Processing task {task.id}, type={task.type.value}")

            # 计算随机间隔
            interval = random.uniform(self.min_interval, self.max_interval)

            try:
                # 执行任务（这里需要根据任务类型调用不同的处理器）
                await self._execute_task(task)

                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                self._completed_tasks[task.id] = task
                del self._running_tasks[task.id]

                logger.info(f"Task {task.id} completed successfully")

            except Exception as e:
                logger.error(f"Task {task.id} failed: {e}")
                task.error = str(e)

                # 判断是否需要重试
                if task.retry_count < task.max_retries:
                    task.status = TaskStatus.RETRYING
                    task.retry_count += 1
                    # 延时后重新加入队列（指数退避）
                    backoff = interval * (2 ** (task.retry_count - 1))
                    logger.info(f"Task {task.id} will retry in {backoff:.1f}s (attempt {task.retry_count}/{task.max_retries})")
                    await asyncio.sleep(backoff)
                    await self._queue.put(task)
                else:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    self._completed_tasks[task.id] = task
                    del self._running_tasks[task.id]
                    logger.error(f"Task {task.id} failed permanently after {task.max_retries} retries")

    async def _execute_task(self, task: Task):
        """执行任务（需要外部注入处理器）"""
        # 这里应该调用实际的任务处理器
        # 为了解耦，处理器通过回调方式注入
        if self._task_handler:
            await self._task_handler(task)
        else:
            # 默认实现：简单延时
            await asyncio.sleep(random.uniform(self.min_interval, self.max_interval))

    def set_task_handler(self, handler: Callable):
        """设置任务处理器"""
        self._task_handler = handler

    @property
    def stats(self) -> dict:
        """获取队列统计"""
        return {
            "pending": self._queue.qsize(),
            "running": len(self._running_tasks),
            "completed": len(self._completed_tasks),
            "max_concurrency": self.max_concurrency
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务状态"""
        if task_id in self._running_tasks:
            return self._running_tasks[task_id]
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id]
        return None


# 全局队列实例
_queue: Optional[BatchedDelayQueue] = None


def get_queue() -> BatchedDelayQueue:
    """获取全局队列实例"""
    global _queue
    if _queue is None:
        from src.core.config import get_config
        config = get_config()
        queue_config = config.queue
        _queue = BatchedDelayQueue(
            max_concurrency=queue_config.get("max_concurrency", 5),
            min_interval=queue_config.get("min_interval_seconds", 10),
            max_interval=queue_config.get("max_interval_seconds", 30),
            max_retries=queue_config.get("max_retries", 3)
        )
    return _queue