"""リソース制限"""
import resource
import signal
import sys
from contextlib import contextmanager
from typing import Optional


class TimeoutError(Exception):
    """タイムアウトエラー"""
    pass


class ResourceLimiter:
    """リソース使用量を制限"""
    
    def __init__(
        self,
        timeout_seconds: int = 10,
        max_memory_mb: int = 2048,
        max_file_size_mb: int = 100,
    ):
        self.timeout = timeout_seconds
        self.max_memory = max_memory_mb * 1024 * 1024
        self.max_file_size = max_file_size_mb * 1024 * 1024
    
    @contextmanager
    def limit(self):
        """リソース制限を適用"""
        # タイムアウト設定（macOSではSIGALRMが使えないため、Unix系のみ）
        old_handler = None
        if sys.platform != 'darwin' and hasattr(signal, 'SIGALRM'):
            def timeout_handler(signum, frame):
                raise TimeoutError(f"実行が{self.timeout}秒を超えました")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
        
        # メモリ制限
        old_mem_limit = resource.getrlimit(resource.RLIMIT_AS)
        # 現在のリミットと最大リミットの小さい方を設定
        if old_mem_limit[1] == resource.RLIM_INFINITY:
            # 無制限の場合は設定値をそのまま使用
            max_mem_limit = self.max_memory
        else:
            max_mem_limit = min(self.max_memory, old_mem_limit[1])
        # 現在のリミットより小さい場合のみ設定（エラーを無視）
        if max_mem_limit < old_mem_limit[0]:
            try:
                resource.setrlimit(resource.RLIMIT_AS, (max_mem_limit, old_mem_limit[1]))
            except (ValueError, OSError):
                # 設定できない場合はスキップ（開発環境など）
                pass
        
        # ファイルサイズ制限
        old_fsize_limit = resource.getrlimit(resource.RLIMIT_FSIZE)
        # 現在のリミットと最大リミットの小さい方を設定
        if old_fsize_limit[1] == resource.RLIM_INFINITY:
            # 無制限の場合は設定値をそのまま使用
            max_fsize_limit = self.max_file_size
        else:
            max_fsize_limit = min(self.max_file_size, old_fsize_limit[1])
        # 現在のリミットより小さい場合のみ設定（エラーを無視）
        if max_fsize_limit < old_fsize_limit[0]:
            try:
                resource.setrlimit(resource.RLIMIT_FSIZE, (max_fsize_limit, old_fsize_limit[1]))
            except (ValueError, OSError):
                # 設定できない場合はスキップ（開発環境など）
                pass
        
        try:
            yield
        finally:
            # 制限を元に戻す
            if old_handler is not None:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
            resource.setrlimit(resource.RLIMIT_AS, old_mem_limit)
            resource.setrlimit(resource.RLIMIT_FSIZE, old_fsize_limit)
