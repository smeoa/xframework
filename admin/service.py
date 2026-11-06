"""Windows 服务封装：把 xf 后端（含前端静态托管）注册为开机自启的系统服务。

管理员权限 PowerShell 下使用：
    python admin\\service.py install
    python admin\\service.py --startup auto update
    python admin\\service.py start
    python admin\\service.py stop
    python admin\\service.py remove

前台调试（不注册服务，直接在当前控制台运行）：
    python admin\\service.py debug
"""

import os
import sys

# SCM 启动服务时工作目录为 C:\Windows\System32；且服务宿主 pythonservice.exe 不解析 venv，
# 其 sys.path 既无项目目录也无 venv 的 site-packages，故在此显式补全。
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADMIN_DIR = os.path.join(PROJECT_ROOT, "admin")
_VENV_SITE = os.path.join(PROJECT_ROOT, ".venv", "Lib", "site-packages")
_PYWIN32_SYSTEM32 = os.path.join(_VENV_SITE, "pywin32_system32")

for _path in (ADMIN_DIR, PROJECT_ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# venv 的 site-packages 及其 .pth 展开的 pywin32 子目录（服务宿主不会自动处理 .pth）
for _path in (
    _VENV_SITE,
    os.path.join(_VENV_SITE, "win32"),
    os.path.join(_VENV_SITE, "win32", "lib"),
    _PYWIN32_SYSTEM32,
):
    if os.path.isdir(_path) and _path not in sys.path:
        sys.path.append(_path)

# pywintypes313.dll / pythoncom313.dll 位于 pywin32_system32，需加入 DLL 搜索路径
if os.path.isdir(_PYWIN32_SYSTEM32) and hasattr(os, "add_dll_directory"):
    os.add_dll_directory(_PYWIN32_SYSTEM32)

import servicemanager
import uvicorn
import win32event
import win32service
import win32serviceutil

# 生产服务端口：与开发用的 APP_PORT 解耦，避免服务与本地开发抢占同一端口。
# 可用 .env 的 SERVICE_PORT 覆盖，未配置时用 8888。
DEFAULT_SERVICE_PORT = 8888


class SyErpService(win32serviceutil.ServiceFramework):
    """xf 后端服务：单进程运行 uvicorn，保证 WebSocket 连接表与导出注册表一致"""

    _svc_name_ = "xf"
    _svc_display_name_ = "xf 后端"
    _svc_description_ = "xf 后端 API + WebSocket + 前端静态托管（FastAPI/uvicorn，单进程）"

    def __init__(self, args):
        super().__init__(args)
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._server = None
        self._log_stream = None

    def _redirect_output(self):
        """服务无控制台，将 stdout/stderr 落盘，便于排查启动与运行日志"""
        log_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        self._log_stream = open(
            os.path.join(log_dir, "service.log"), "a", encoding="utf-8", buffering=1
        )
        sys.stdout = self._log_stream
        sys.stderr = self._log_stream

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogInfoMsg("xf: 收到停止指令")
        if self._server is not None:
            self._server.should_exit = True
        win32event.SetEvent(self._stop_event)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg("xf: 服务启动")
        self._redirect_output()

        from framework import config

        # 先导入 main，使其 module 级初始化（sys.path / 事件循环策略）先于 uvicorn 建连生效
        import main as app_main

        host = config.get("APP_HOST", "0.0.0.0")
        # 服务端口独立于开发的 APP_PORT(8000)，便于本机同时跑开发服务
        port = config.get_int("SERVICE_PORT", DEFAULT_SERVICE_PORT)

        uvicorn_config = uvicorn.Config(
            app_main.app,
            host=host,
            port=port,
            reload=False,  # 服务模式不支持热重载
            workers=1,     # WebSocket 连接表 / 导出注册表为进程内存态，必须单进程
            log_level=config.get("LOG_LEVEL", "info").lower(),
        )
        self._server = uvicorn.Server(uvicorn_config)
        self._server.run()
        servicemanager.LogInfoMsg("xf: 服务已退出")


def _service_pythonpath():
    """服务宿主 pythonservice.exe 以基础解释器启动、且以 LocalSystem 身份运行，
    既不加载 venv 的 .pth，也读不到当前用户的 site-packages。
    故把项目目录、venv 与用户级 site-packages（含 pywin32 子目录）显式并入 PYTHONPATH。"""
    import site

    paths = [PROJECT_ROOT, ADMIN_DIR, _VENV_SITE]
    user_site = site.getusersitepackages()
    if isinstance(user_site, str):
        paths += [
            user_site,
            os.path.join(user_site, "win32"),
            os.path.join(user_site, "win32", "lib"),
            os.path.join(user_site, "pywin32_system32"),
        ]
    return os.pathsep.join(p for p in paths if os.path.isdir(p))


def _write_service_environment():
    """把 PYTHONPATH 写入服务注册表项（HKLM\\...\\Services\\<name>\\Environment），
    由 SCM 在启动服务时注入进程环境；需管理员权限。"""
    import winreg

    value = "PYTHONPATH=" + _service_pythonpath()
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Services\%s" % SyErpService._svc_name_,
            0,
            winreg.KEY_SET_VALUE,
        )
    except OSError as exc:
        print("警告：未能写入服务环境变量（需管理员权限）:", exc)
        return
    try:
        winreg.SetValueEx(key, "Environment", 0, winreg.REG_MULTI_SZ, [value])
        print("已写入服务环境变量 Environment:", value)
    finally:
        winreg.CloseKey(key)


if __name__ == "__main__":
    _argv = sys.argv[1:]
    win32serviceutil.HandleCommandLine(SyErpService)
    if any(_cmd in ("install", "update") for _cmd in _argv):
        _write_service_environment()
