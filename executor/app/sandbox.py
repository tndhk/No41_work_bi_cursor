"""サンドボックス実装"""
import sys
import importlib
import importlib.util
import builtins
from typing import List, Set
from contextlib import contextmanager


# 許可ライブラリのホワイトリスト
ALLOWED_MODULES: Set[str] = {
    # 標準ライブラリ
    "builtins",
    "codecs",
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
        self.original_import = builtins.__import__
    
    def __enter__(self):
        """コンテキストマネージャー開始"""
        builtins.__import__ = self._import_hook
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        builtins.__import__ = self.original_import
    
    def _import_hook(self, name, globals=None, locals=None, fromlist=(), level=0):
        """importフック実装"""
        # 相対インポート（level > 0）の場合は、globalsから親モジュールを確認
        if level > 0 and globals and '__name__' in globals:
            # 相対インポートは、親モジュールが許可されている場合は許可
            parent_module = globals['__name__'].rsplit('.', level)[0] if '.' in globals['__name__'] else globals['__name__']
            base_module = parent_module.split('.')[0]
            if base_module in self.allowed_modules or base_module.startswith('_'):
                return self.original_import(name, globals, locals, fromlist, level)
        
        # モジュール名をチェック
        module_name = name.split('.')[0]
        
        # 内部モジュール（_で始まる）は許可
        if module_name.startswith('_'):
            return self.original_import(name, globals, locals, fromlist, level)
        
        # ホワイトリストチェック
        if module_name not in self.allowed_modules:
            # サブモジュールのチェック（例: pandas.io）
            parts = name.split('.')
            if len(parts) > 1:
                base_module = parts[0]
                if base_module in self.allowed_modules:
                    # ベースモジュールが許可されている場合は許可
                    return self.original_import(name, globals, locals, fromlist, level)
            
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
