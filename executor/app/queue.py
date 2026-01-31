"""実行キュー管理"""
import asyncio
from typing import Callable, Any, Dict
from dataclasses import dataclass
from enum import Enum


class QueueFullError(Exception):
    """キュー満杯エラー"""
    pass


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """タスク"""
    task_id: str
    func: Callable
    status: TaskStatus = TaskStatus.PENDING


class ExecutionQueue:
    """実行キュー"""
    
    def __init__(self, max_concurrent: int = 10, queue_size: int = 50):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.worker_task: asyncio.Task = None
    
    async def submit(self, task_id: str, func: Callable) -> None:
        """タスクをキューに追加"""
        if self.queue.full():
            raise QueueFullError(f"Queue is full (size: {self.queue_size})")
        
        task = Task(task_id=task_id, func=func)
        await self.queue.put(task)
    
    async def _worker(self):
        """ワーカーループ"""
        while True:
            try:
                task = await self.queue.get()
                
                # 同時実行数制限チェック
                while len(self.running_tasks) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                
                # タスクを実行
                task.status = TaskStatus.RUNNING
                coro = task.func() if asyncio.iscoroutinefunction(task.func) else asyncio.to_thread(task.func)
                running_task = asyncio.create_task(coro)
                self.running_tasks[task.task_id] = running_task
                
                def cleanup(task_id):
                    def _cleanup(fut):
                        if task_id in self.running_tasks:
                            del self.running_tasks[task_id]
                    return _cleanup
                
                running_task.add_done_callback(cleanup(task.task_id))
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                # エラーをログに記録（実装時）
                pass
    
    def start(self):
        """ワーカーを開始"""
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())
    
    def stop(self):
        """ワーカーを停止"""
        if self.worker_task and not self.worker_task.done():
            self.worker_task.cancel()
    
    def is_full(self) -> bool:
        """キューが満杯かどうか"""
        return self.queue.full()
