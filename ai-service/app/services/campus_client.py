"""HTTP 客户端 — 透传 JWT 调用 campus-service 内部接口。"""

import logging
from typing import Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# 超时设置（秒）
REQUEST_TIMEOUT = 10.0


class CampusClient:
    """HTTP 客户端，透传 JWT 调用 campus-service 内部接口。

    所有方法将前端用户的 JWT 原样传递给 campus-service，
    campus-service 解析 JWT 获取 student_id 保证数据隔离。
    """

    def __init__(self) -> None:
        """初始化 CampusClient，创建异步 HTTP 客户端。"""
        self.base_url = settings.CAMPUS_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)

    async def get_schedule(self, token: str) -> Optional[dict]:
        """查询课表 — 调用 GET /api/campus/internal/schedule。

        Args:
            token: 用户 JWT token（将原样透传给 campus-service）

        Returns:
            Optional[dict]: 课表数据，接口异常时返回 None
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/campus/internal/schedule",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"课表查询成功, 返回数据条数: {len(data.get('data', []))}")
            return data
        except httpx.TimeoutException:
            logger.warning("课表查询超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"课表查询 HTTP 错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"课表查询异常: {e}", exc_info=True)
            return None

    async def get_repair(self, token: str) -> Optional[dict]:
        """查询宿舍报修工单 — 调用 GET /api/campus/internal/repair。

        Args:
            token: 用户 JWT token

        Returns:
            Optional[dict]: 报修数据，接口异常时返回 None
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/campus/internal/repair",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"报修查询成功, 返回数据条数: {len(data.get('data', []))}")
            return data
        except httpx.TimeoutException:
            logger.warning("报修查询超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"报修查询 HTTP 错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"报修查询异常: {e}", exc_info=True)
            return None

    async def get_scholarship(self, token: str) -> Optional[dict]:
        """查询奖助记录 — 调用 GET /api/campus/internal/scholarship。

        Args:
            token: 用户 JWT token

        Returns:
            Optional[dict]: 奖助数据，接口异常时返回 None
        """
        try:
            response = await self.client.get(
                f"{self.base_url}/api/campus/internal/scholarship",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"奖助查询成功, 返回数据条数: {len(data.get('data', []))}")
            return data
        except httpx.TimeoutException:
            logger.warning("奖助查询超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"奖助查询 HTTP 错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"奖助查询异常: {e}", exc_info=True)
            return None

    async def get_notices(self, token: str, keyword: str = "") -> Optional[dict]:
        """检索校园通知 — 调用 GET /api/campus/internal/notices。

        Args:
            token: 用户 JWT token
            keyword: 搜索关键词

        Returns:
            Optional[dict]: 通知数据，接口异常时返回 None
        """
        try:
            params = {}
            if keyword:
                params["keyword"] = keyword
            response = await self.client.get(
                f"{self.base_url}/api/campus/internal/notices",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"通知查询成功, keyword={keyword}")
            return data
        except httpx.TimeoutException:
            logger.warning("通知查询超时")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"通知查询 HTTP 错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"通知查询异常: {e}", exc_info=True)
            return None

    async def close(self) -> None:
        """关闭 HTTP 客户端连接。"""
        await self.client.aclose()
