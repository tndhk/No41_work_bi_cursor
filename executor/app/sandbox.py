"""サンドボックス実装"""
import sys
import importlib
import importlib.util
from typing import List, Set
from contextlib import contextmanager


# 許可ライブラリのホワイトリスト
ALLOWED_MODULES: Set[str] = {
    # 標準ライブラリ
    "builtins",
    "collections",
    "datetime",
    "json",
    "math",
    "random",
    "re",
    "string",
    "typing",
    "uuid",
    
    # データ処理
    "pandas",
    "numpy",
    "pyarrow",
    "pyarrow.parquet",
    
    # 可視化
    "plotly",
    "plotly.graph_objects",
    "plotly.express",
    "matplotlib",
    "matplotlib.pyplot",
    "seaborn",
}


class SandboxError(Exception):
    """サンドボックスエラー"""
    pass


class ImportHook:
    """importフック（ホワイトリストチェック）"""
    
    def __init__(self, allowed_modules: Set[str]):
        self.allowed_modules = allowed_modules
        self.original_import = __builtins__.__import__
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        __builtins__.__import__ = self._import_hook
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        __builtins__.__import__ = self.original_import
    
    def _import_hook(self, name, globals=None, locals=None, fromlist=(), level=0):
        """importフック実装"""
        # モジュール名をチェック
        module_name = name.split('.')[0]
        
        if module_name not in self.allowed_modules:
            raise SandboxError(
                f"Import of '{name}' is not allowed. "
                f"Only whitelisted modules are permitted."
            )
        
        # 許可されたモジュールのみインポート
        return self.original_import(name, globals, locals, fromlist, level)


@contextmanager
def sandbox_context():
    """サンドボックスコンテキスト"""
    with ImportHook(ALLOWED_MODULES):
        yield


def validate_code(code: str) -> List[str]:
    """コードを検証（危険な操作をチェック）"""
    errors = []
    
    # 危険なキーワードをチェック
    dangerous_keywords = [
        "eval",
        "exec",
        "__import__",
        "open(",
        "file(",
        "input(",
        "raw_input(",
        "compile(",
    ]
    
    for keyword in dangerous_keywords:
        if keyword in code:
            errors.append(f"Dangerous keyword '{keyword}' is not allowed")
    
    return errors
