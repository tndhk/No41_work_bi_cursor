"""カスタム例外"""
from fastapi import HTTPException, status


class BIException(HTTPException):
    """ベース例外クラス"""
    pass


class BadRequestError(BIException):
    """不正なリクエストエラー"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "BAD_REQUEST",
                "message": detail,
            },
        )


class ValidationError(BIException):
    """バリデーションエラー"""
    def __init__(self, detail: str, field: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VALIDATION_ERROR",
                "message": detail,
                "field": field,
            },
        )


class NotFoundError(BIException):
    """リソース不存在エラー"""
    def __init__(self, resource: str, resource_id: str = None):
        detail = f"{resource} not found"
        if resource_id:
            detail += f": {resource_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": detail,
            },
        )


class ForbiddenError(BIException):
    """権限エラー"""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": detail,
            },
        )


class UnauthorizedError(BIException):
    """認証エラー"""
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": detail,
            },
        )


class ExecutionError(BIException):
    """実行エラー"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "EXECUTION_ERROR",
                "message": detail,
            },
        )


class ExecutionTimeoutError(BIException):
    """実行タイムアウトエラー"""
    def __init__(self, detail: str = "Execution timeout"):
        super().__init__(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                "code": "EXECUTION_TIMEOUT",
                "message": detail,
            },
        )


class InternalError(BIException):
    """内部エラー"""
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": detail,
            },
        )
