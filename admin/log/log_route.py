"""系统日志路由模块

提供系统日志的列表、详情、统计、删除、批量删除、清理接口（全部为 POST）。
接口命名与 admin/collectqueue 模块保持一致。
"""

from fastapi import APIRouter, Depends, Request

from framework.core.auth import require_permission

from .log_controller import LogController

# 创建主路由
router = APIRouter(prefix="/admin/log", tags=["系统日志"])


@router.post("/get-log-list", summary="获取系统日志列表", dependencies=[Depends(require_permission("log:list"))])
async def get_log_list_api(request: Request):
    """获取系统日志列表

    Returns:
        列表响应
    """
    controller = LogController(request)
    return await controller.list()


@router.post("/get-log", summary="获取系统日志详情", dependencies=[Depends(require_permission("log:list"))])
async def get_log_api(request: Request):
    """获取系统日志详情

    Returns:
        详情响应
    """
    controller = LogController(request)
    return await controller.detail()


@router.post("/get-log-stats", summary="获取日志统计（各级别条数 + 落库组件状态）", dependencies=[Depends(require_permission("log:list"))])
async def get_log_stats_api(request: Request):
    """获取日志统计

    Returns:
        统计响应
    """
    controller = LogController(request)
    return await controller.stats()


@router.post("/write-log", summary="外部程序写入日志（采集脚本等）", dependencies=[Depends(require_permission("log:write"))])
async def write_log_api(request: Request):
    """外部程序写入日志

    采集脚本 / 定时任务等外部程序调用；级别低于配置 LOG_LEVEL 的记录不落库。

    Returns:
        写入结果响应
    """
    controller = LogController(request)
    return await controller.write_log()


@router.post("/delete-log", summary="删除系统日志", dependencies=[Depends(require_permission("log:delete"))])
async def delete_log_api(request: Request):
    """删除系统日志

    Returns:
        删除结果响应
    """
    controller = LogController(request)
    return await controller.delete()


@router.post("/batch-log", summary="批量删除指定ID的系统日志", dependencies=[Depends(require_permission("log:delete"))])
async def batch_log_api(request: Request):
    """批量删除指定ID的系统日志

    Returns:
        删除结果响应
    """
    controller = LogController(request)
    return await controller.batch_log()


@router.post("/batch-all-log", summary="删除所有符合筛选条件的系统日志", dependencies=[Depends(require_permission("log:delete"))])
async def batch_all_log_api(request: Request):
    """删除所有符合筛选条件的系统日志

    Returns:
        删除结果响应
    """
    controller = LogController(request)
    return await controller.batch_all_log()


@router.post("/clean-log", summary="清理N天前的系统日志（物理删除，仅管理员）", dependencies=[Depends(require_permission("log:clean"))])
async def clean_log_api(request: Request):
    """清理N天前的系统日志

    Returns:
        清理结果响应
    """
    controller = LogController(request)
    return await controller.clean_log()
