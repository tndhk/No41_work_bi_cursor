"""サンドボックス実装"""
import ast
import builtins
from typing import List, Set
from contextlib import contextmanager


# 許可ライブラリのホワイトリスト
ALLOWED_MODULES: Set[str] = {
    # 標準ライブラリ
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
        # 相対インポートは許可しない
        if level > 0:
            raise SandboxError("Relative imports are not allowed")
        
        # モジュール名をチェック
        module_name = name.split('.')[0]
        
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


def build_safe_builtins() -> dict:
    """安全な組み込み関数のホワイトリスト"""
    allowed_names = {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "filter",
        "float",
        "int",
        "len",
        "list",
        "map",
        "max",
        "min",
        "print",
        "range",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "zip",
    }
    safe = {}
    for name in allowed_names:
        safe[name] = getattr(builtins, name)
    return safe


def validate_code(code: str) -> List[str]:
    """コードを検証（危険な操作をチェック）"""
    errors = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Syntax error: {e}"]

    forbidden_names = {
        "eval",
        "exec",
        "__import__",
        "open",
        "compile",
        "input",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    errors.append("Relative imports are not allowed")
                    continue
                module_name = node.module.split('.')[0] if node.module else ""
                if module_name not in ALLOWED_MODULES:
                    errors.append(f"Import of '{node.module}' is not allowed")
            else:
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name not in ALLOWED_MODULES:
                        errors.append(f"Import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__"):
                errors.append("Access to dunder attributes is not allowed")
        elif isinstance(node, ast.Name):
            if node.id in forbidden_names:
                errors.append(f"Use of '{node.id}' is not allowed")
            if node.id.startswith("__") and node.id.endswith("__"):
                errors.append("Use of dunder names is not allowed")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                errors.append(f"Call to '{node.func.id}' is not allowed")

    return errors
