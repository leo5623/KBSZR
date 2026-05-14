"""任务队列模块测试"""
import pytest
import asyncio
from src.queue.task_queue import (
    BatchedDelayQueue, Task, TaskStatus, TaskType
)


class TestTask:
    """Task数据类测试"""

    def test_task_creation_default_values(self):
        """测试任务默认属性"""
        task = Task(type=TaskType.TTS)

        assert task.id is not None
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 0
        assert task.max_retries == 3
        assert task.data == {}
        assert task.created_at is not None
        assert task.started_at is None
        assert task.completed_at is None

    def test_task_to_dict(self):
        """测试任务序列化"""
        task = Task(type=TaskType.TTS, data={"key": "value"})
        task_dict = task.to_dict()

        assert task_dict["type"] == "tts"
        assert task_dict["status"] == "pending"
        assert task_dict["data"] == {"key": "value"}
        assert "id" in task_dict
        assert "created_at" in task_dict


@pytest.mark.asyncio
class TestBatchedDelayQueue:
    """BatchedDelayQueue测试"""

    async def test_queue_initialization(self):
        """测试队列初始化"""
        queue = BatchedDelayQueue(
            max_concurrency=3,
            min_interval=1,
            max_interval=2,
            max_retries=2
        )

        assert queue.max_concurrency == 3
        assert queue.min_interval == 1
        assert queue.max_interval == 2
        assert queue.max_retries == 2

    async def test_add_single_task(self):
        """测试添加单个任务"""
        queue = BatchedDelayQueue(max_concurrency=1)

        task = Task(type=TaskType.TTS)
        task_id = await queue.add_task(task)

        assert task_id == task.id
        assert queue.stats["pending"] == 1

    async def test_add_multiple_tasks(self):
        """测试批量添加任务"""
        queue = BatchedDelayQueue(max_concurrency=5)

        tasks = [Task(type=TaskType.TTS) for _ in range(3)]
        task_ids = await queue.add_tasks(tasks)

        assert len(task_ids) == 3
        assert queue.stats["pending"] == 3

    async def test_start_and_stop(self):
        """测试队列启动停止"""
        queue = BatchedDelayQueue(max_concurrency=2)
        await queue.start()

        assert queue._is_running is True
        assert len(queue._workers) == 2

        await queue.stop()
        assert queue._is_running is False

    async def test_task_handler_setter(self):
        """测试任务处理器设置"""
        queue = BatchedDelayQueue(max_concurrency=1)

        async def dummy_handler(task):
            pass

        queue.set_task_handler(dummy_handler)
        assert queue._task_handler is dummy_handler

    async def test_get_task_not_exists(self):
        """测试获取不存在的任务"""
        queue = BatchedDelayQueue()

        result = queue.get_task("nonexistent-id")
        assert result is None

    async def test_stats(self):
        """测试统计信息"""
        queue = BatchedDelayQueue(max_concurrency=5)

        stats = queue.stats
        assert "pending" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "max_concurrency" in stats