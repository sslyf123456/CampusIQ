import logging

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("campus_service")


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFound(AppException):
    def __init__(self, entity: str):
        super().__init__(404, f"{entity}不存在")


class Unauthorized(AppException):
    def __init__(self, detail: str = "未登录或登录已过期"):
        super().__init__(401, detail)


class Forbidden(AppException):
    def __init__(self, detail: str = "无权限执行此操作"):
        super().__init__(403, detail)


class BadRequest(AppException):
    def __init__(self, detail: str):
        super().__init__(400, detail)


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(
        "数据库错误 [%s %s] %s: %s",
        request.method,
        request.url.path,
        exc.__class__.__name__,
        str(exc.orig).splitlines()[0] if exc.orig else str(exc).splitlines()[0],
    )
    return JSONResponse(status_code=503, content={"detail": "数据库服务不可用，请稍后重试"})


async def general_exception_handler(request: Request, exc: Exception):
    logger.error("未处理异常 [%s %s] %s", request.method, request.url.path, exc.__class__.__name__)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """将 Pydantic 422 校验错误转为统一的 {"detail": "..."} 格式"""
    msg_map = {
        # 必填/缺失
        "Field required": "该字段为必填项",
        "Missing": "缺少必要参数",
        "Extra inputs are not permitted": "传入了多余的字段",
        # 类型转换
        "Input should be a valid decimal": "请输入有效的数字",
        "Input should be a valid integer": "请输入有效的整数",
        "Input should be a valid number": "请输入有效的数字",
        "Input should be a valid string": "请输入有效的文本",
        "Input should be a valid boolean": "请输入有效的布尔值",
        "Input should be a valid date": "请输入有效的日期",
        "Input should be a valid datetime": "请输入有效的日期时间",
        "Input should be a valid list": "请输入有效的列表",
        "Input should be a valid dictionary": "请输入有效的对象",
        "Input should be a valid email": "请输入有效的邮箱地址",
        "Input should be a valid URL": "请输入有效的网址",
        "Input should be a valid UUID": "请输入有效的UUID",
        # JSON 解析
        "JSON decode error": "JSON格式错误",
        "Expecting value": "JSON格式错误，无法解析",
        # 字符串长度
        "String should have at least 1 character": "内容不能为空",
        "String should have at least {min_length} characters": "长度不足",
        "String should have at most {max_length} characters": "内容超出长度限制",
        "ensure this value has at least 1 characters": "长度不能为空",
        "string too long": "内容超出长度限制",
        # 数字范围
        "Input should be greater than 0": "必须大于0",
        "Input should be greater than or equal to 0": "不能小于0",
        "Input should be less than": "数值超出上限",
        "Input should be less than or equal to": "数值超出上限",
        "ensure this value is greater than": "数值过小",
        "ensure this value is greater than or equal to": "数值过小",
        "ensure this value is less than": "数值过大",
        "ensure this value is less than or equal to": "数值过大",
        # 枚举/正则
        "Input should be": "值不合法",
        "value is not a valid enumeration member": "值不在允许范围内",
        "String should match pattern": "格式不正确",
        "String does not match pattern": "格式不正确",
        # 日期/时间逻辑
        "Input should be a valid date in the future": "日期应在未来",
        "Input should be a valid date in the past": "日期应在过去",
        # 其他
        "Invalid input": "输入无效",
        "Value error": "值错误",
        "Assertion failed": "校验失败",
    }
    errors = exc.errors()
    if errors:
        first = errors[0]
        loc = ".".join(str(l) for l in first.get("loc", []) if l not in ("body",))
        raw_msg = first.get("msg", "参数错误")
        # 精确匹配
        msg = msg_map.get(raw_msg)
        if not msg:
            # 前缀模糊匹配（Pydantic v2 的动态参数消息）
            for key, val in msg_map.items():
                if raw_msg.startswith(key) or key in raw_msg:
                    msg = val
                    break
        if not msg:
            msg = raw_msg
        detail = f"{loc}: {msg}" if loc else msg
    else:
        detail = "请求参数错误"
    return JSONResponse(status_code=422, content={"detail": detail})
