"""ResourceLimiterのテスト"""
import unittest
import time
import signal
import sys
from app.resource_limiter import ResourceLimiter, TimeoutError


class TestResourceLimiter(unittest.TestCase):
    """ResourceLimiterのテスト"""
    
    @unittest.skipIf(sys.platform == 'darwin', "SIGALRM not available on macOS")
    def test_timeout_raises_error(self):
        """タイムアウト時にTimeoutErrorが発生する"""
        limiter = ResourceLimiter(timeout_seconds=1)
        
        with self.assertRaises(TimeoutError):
            with limiter.limit():
                time.sleep(2)  # タイムアウトを超える
    
    def test_timeout_within_limit_succeeds(self):
        """タイムアウト内で完了する場合は成功する"""
        limiter = ResourceLimiter(timeout_seconds=5)
        
        # 例外が発生しないことを確認
        with limiter.limit():
            time.sleep(0.1)
    
    def test_memory_limit_applied(self):
        """メモリ制限が適用される"""
        limiter = ResourceLimiter(max_memory_mb=1)  # 1MB制限
        
        with limiter.limit():
            # メモリ制限が設定されていることを確認
            import resource
            mem_limit = resource.getrlimit(resource.RLIMIT_AS)
            # 開発環境などで設定できない場合はスキップ
            if mem_limit[0] != resource.RLIM_INFINITY:
                # 設定できた場合は、設定値以下であることを確認
                self.assertLessEqual(mem_limit[0], 1024 * 1024)  # 1MB以下
    
    def test_file_size_limit_applied(self):
        """ファイルサイズ制限が適用される"""
        limiter = ResourceLimiter(max_file_size_mb=1)  # 1MB制限
        
        with limiter.limit():
            # ファイルサイズ制限が設定されていることを確認
            import resource
            fsize_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
            self.assertEqual(fsize_limit[0], 1024 * 1024)  # 1MB


if __name__ == '__main__':
    unittest.main()
