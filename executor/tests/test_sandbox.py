"""Sandboxのテスト"""
import unittest
from app.sandbox import sandbox_context, validate_code, SandboxError


class TestSandbox(unittest.TestCase):
    """Sandboxのテスト"""
    
    def test_validate_code_detects_dangerous_keywords(self):
        """validate_codeが危険キーワードを検出する"""
        code = "eval('print(1)')"
        errors = validate_code(code)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any('eval' in error for error in errors))
    
    def test_validate_code_allows_safe_code(self):
        """validate_codeが安全なコードを許可する"""
        code = "import pandas as pd\ndf = pd.DataFrame()"
        errors = validate_code(code)
        self.assertEqual(len(errors), 0)

    def test_validate_code_blocks_dunder_access(self):
        """dunder属性へのアクセスを拒否する"""
        code = "x = ().__class__"
        errors = validate_code(code)
        self.assertGreater(len(errors), 0)

    def test_validate_code_blocks_disallowed_import(self):
        """許可されていないimportを拒否する"""
        code = "import os"
        errors = validate_code(code)
        self.assertGreater(len(errors), 0)
    
    def test_sandbox_context_blocks_disallowed_import(self):
        """sandbox_contextが許可されていないimportを拒否する"""
        with self.assertRaises(SandboxError):
            with sandbox_context():
                import os  # 許可されていないモジュール
    
    def test_sandbox_context_allows_whitelisted_import(self):
        """sandbox_contextがホワイトリストのimportを許可する"""
        # 例外が発生しないことを確認（標準ライブラリを使用）
        try:
            with sandbox_context():
                import json  # 許可されている標準ライブラリモジュール
        except SandboxError:
            self.fail("SandboxError should not be raised for whitelisted module")


if __name__ == '__main__':
    unittest.main()
