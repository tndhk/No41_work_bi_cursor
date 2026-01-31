"""ExecutionQueueのテスト"""
import unittest
import asyncio
from app.queue import ExecutionQueue, QueueFullError


class TestExecutionQueue(unittest.TestCase):
    """ExecutionQueueのテスト"""
    
    def test_queue_full_raises_error(self):
        """キューが満杯時にQueueFullErrorが発生する"""
        queue = ExecutionQueue(max_concurrent=1, queue_size=1)
        
        async def test():
            # キューを満杯にする
            await queue.submit("task1", lambda: None)
            
            # 2つ目でエラーが発生するはず（キューサイズが1のため）
            with self.assertRaises(QueueFullError):
                await queue.submit("task2", lambda: None)
        
        asyncio.run(test())
    
    def test_queue_accepts_within_limit(self):
        """キューが上限内の場合は受け入れる"""
        queue = ExecutionQueue(max_concurrent=2, queue_size=5)
        
        async def test():
            # 上限内のタスクを追加
            await queue.submit("task1", lambda: None)
            await queue.submit("task2", lambda: None)
            # エラーが発生しないことを確認
        
        asyncio.run(test())


if __name__ == '__main__':
    unittest.main()
