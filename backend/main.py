#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teacher Assistant AI - 统一启动脚本
一键启动所有后端服务

用法:
    python main.py                    # 启动所有服务
    python main.py --help             # 显示帮助信息
    python main.py --log-level DEBUG  # 设置日志级别
    python main.py --sequential       # 顺序启动而非并行

"""

import os
import sys
import time
import signal
import logging
import argparse
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ServiceConfig:
    """服务配置类"""
    name: str
    display_name: str
    file_path: str
    port: int
    process: Optional[subprocess.Popen] = None
    status: str = "pending"  # pending, starting, running, failed, stopped
    start_time: Optional[datetime] = None
    pid: Optional[int] = None
    error_message: Optional[str] = None
    log_file: Optional[str] = None  # 服务日志文件路径
    command_type: str = "python"  # python 或 node
    working_dir: Optional[str] = None  # 工作目录（用于Node.js项目）
    startup_command: Optional[List[str]] = None  # 自定义启动命令


@dataclass
class StartupLog:
    """启动日志记录"""
    timestamp: datetime
    service_name: str
    event: str
    details: str = ""


class ServiceLauncher:
    """服务启动管理器"""

    @staticmethod
    def _get_service_path(*path_parts: str) -> str:
        """获取基于当前文件目录的服务路径"""
        return str(Path(__file__).parent.joinpath(*path_parts).resolve())

    # 服务配置列表 - 包含新增的讨论区服务和认证服务
    SERVICES_CONFIG: List[ServiceConfig] = [
        ServiceConfig(
            name="login",
            display_name="登录服务",
            file_path=_get_service_path.__func__("Login", "login.py"),
            port=5000,
            startup_command=[sys.executable, _get_service_path.__func__("Login", "login.py")]
        ),
        ServiceConfig(
            name="openmaic",
            display_name="OpenMAIC智能课堂服务",
            file_path=_get_service_path.__func__("OpenMAIC", "package.json"),
            port=5006,
            startup_command=["pnpm", "dev", "--port", "5006"],
            command_type="node",
            working_dir=_get_service_path.__func__("OpenMAIC")
        ),
        ServiceConfig(
            name="api_management",
            display_name="API统一管理服务",
            file_path=_get_service_path.__func__("API_management", "app.py"),
            port=5010,
            startup_command=[sys.executable, _get_service_path.__func__("API_management", "app.py"), "--host", "0.0.0.0", "--port", "5010"]
        ),
        ServiceConfig(
            name="digit_recognition",
            display_name="手写数字识别服务(GPU)",
            file_path=_get_service_path.__func__("DigitRecognition", "app.py"),
            port=5005,
            startup_command=[sys.executable, _get_service_path.__func__("DigitRecognition", "app.py")]
        ),
        ServiceConfig(
            name="practice_service",
            display_name="练习反馈服务",
            file_path=_get_service_path.__func__("PracticeService", "app.py"),
            port=5011,
            startup_command=[sys.executable, _get_service_path.__func__("PracticeService", "app.py")]
        ),
        # 新增讨论区服务
        ServiceConfig(
            name="discussion",
            display_name="讨论区服务",
            file_path=_get_service_path.__func__("Discussion", "app.py"),
            port=5020,
            startup_command=[sys.executable, _get_service_path.__func__("Discussion", "app.py"), "--port", "5020"]
        ),
        # 新增多方式认证服务
        ServiceConfig(
            name="auth_multi",
            display_name="多方式认证服务",
            file_path=_get_service_path.__func__("AuthMulti", "app.py"),
            port=5021,
            startup_command=[sys.executable, _get_service_path.__func__("AuthMulti", "app.py"), "--port", "5021"]
        ),
        # 新增社交服务（个人主页/关注/私信）
        ServiceConfig(
            name="social",
            display_name="社交服务",
            file_path=_get_service_path.__func__("Social", "app.py"),
            port=5022,
            startup_command=[sys.executable, _get_service_path.__func__("Social", "app.py"), "--port", "5022"]
        ),
    ]

    def __init__(self, log_level: str = "INFO", sequential: bool = False):
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.sequential = sequential
        self.services: Dict[str, ServiceConfig] = {}
        self.logs: List[StartupLog] = []
        self.shutdown_event = threading.Event()
        self._cleanup_old_logs()
        self.logger = self._setup_logger()
        self._setup_signal_handlers()
        self._init_services()

    def _setup_logger(self) -> logging.Logger:
        """配置日志记录器"""
        logger = logging.getLogger("ServiceLauncher")
        logger.setLevel(self.log_level)

        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)

            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            self.log_file = log_file

        return logger

    def _setup_signal_handlers(self):
        """设置信号处理器以实现优雅关闭"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        if sys.platform == 'win32':
            try:
                signal.signal(signal.SIGBREAK, self._signal_handler)
            except AttributeError:
                pass

    def _signal_handler(self, signum, frame):
        """信号处理函数"""
        sig_name = signal.Signals(signum).name if hasattr(signal, 'Signals') else str(signum)
        self.logger.info(f"\n收到信号 {sig_name}，开始优雅关闭服务...")
        self.shutdown_event.set()
        self.stop_all_services()
        sys.exit(0)

    def _init_services(self):
        """初始化服务配置"""
        for config in self.SERVICES_CONFIG:
            self.services[config.name] = config

    def _cleanup_old_logs(self):
        """
        日志轮转清理机制
        """
        log_dir = Path(__file__).parent / "logs"
        if not log_dir.exists():
            return

        try:
            from collections import defaultdict
            time_groups = defaultdict(list)

            for log_file in log_dir.glob("startup_*.log"):
                parts = log_file.stem.split('_')
                if len(parts) >= 3:
                    timestamp = f"{parts[1]}_{parts[2]}"
                    time_groups[timestamp].append(log_file)

            services_dir = log_dir / "services"
            if services_dir.exists():
                for log_file in services_dir.glob("*.log"):
                    parts = log_file.stem.split('_')
                    if len(parts) >= 3:
                        timestamp = f"{parts[-2]}_{parts[-1]}"
                        time_groups[timestamp].append(log_file)

            if len(time_groups) <= 2:
                return

            sorted_timestamps = sorted(time_groups.keys(), reverse=True)
            timestamps_to_delete = sorted_timestamps[2:]

            deleted_count = 0
            for timestamp in timestamps_to_delete:
                for log_file in time_groups[timestamp]:
                    try:
                        log_file.unlink()
                        deleted_count += 1
                    except OSError as e:
                        print(f"[日志清理警告] 无法删除文件 {log_file}: {e}", file=sys.stderr)

            if deleted_count > 0:
                print(f"[日志清理] 已删除 {deleted_count} 个旧日志文件，保留最近两次运行的日志")

        except Exception as e:
            print(f"[日志清理警告] 日志清理过程中发生错误: {e}", file=sys.stderr)

    def _log_event(self, service_name: str, event: str, details: str = ""):
        """记录启动事件"""
        log_entry = StartupLog(
            timestamp=datetime.now(),
            service_name=service_name,
            event=event,
            details=details
        )
        self.logs.append(log_entry)

    def _validate_service_file(self, config: ServiceConfig) -> Tuple[bool, str]:
        """验证服务文件是否存在且可访问"""
        file_path = Path(config.file_path)

        if not file_path.exists():
            return False, f"文件不存在: {config.file_path}"

        if not file_path.is_file():
            return False, f"路径不是文件: {config.file_path}"

        if not file_path.suffix == '.py':
            return False, f"文件不是Python脚本: {config.file_path}"

        return True, ""

    def _start_single_service(self, config: ServiceConfig) -> ServiceConfig:
        """启动单个服务"""
        service_name = config.display_name

        if config.command_type == "node":
            is_valid, error_msg = self._validate_node_service(config)
            if not is_valid:
                config.status = "failed"
                config.error_message = error_msg
                self.logger.error(f"[{service_name}] 验证失败: {error_msg}")
                self._log_event(service_name, "VALIDATION_FAILED", error_msg)
                return config
        elif config.startup_command:
            pass
        else:
            is_valid, error_msg = self._validate_service_file(config)
            if not is_valid:
                config.status = "failed"
                config.error_message = error_msg
                self.logger.error(f"[{service_name}] 验证失败: {error_msg}")
                self._log_event(service_name, "VALIDATION_FAILED", error_msg)
                return config

        try:
            config.status = "starting"
            config.start_time = datetime.now()
            self._log_event(service_name, "STARTING", f"Port: {config.port}")

            log_dir = Path(__file__).parent / "logs" / "services"
            log_dir.mkdir(parents=True, exist_ok=True)
            service_log_file = log_dir / f"{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            with open(service_log_file, 'w', encoding='utf-8') as log_file:
                if config.command_type == "node" and config.startup_command:
                    cmd = ' '.join(config.startup_command)
                    startup_info = f"命令: {cmd}, 工作目录: {config.working_dir}"
                    self.logger.info(f"[{service_name}] 启动命令: {startup_info}")
                    use_shell = True
                elif config.startup_command:
                    cmd = config.startup_command
                    startup_info = f"命令: {' '.join(cmd)}"
                    self.logger.info(f"[{service_name}] 启动命令: {startup_info}")
                    use_shell = False
                else:
                    python_exe = sys.executable
                    cmd = [python_exe, config.file_path]
                    use_shell = False

                popen_kwargs = {
                    'stdout': log_file,
                    'stderr': subprocess.STDOUT,
                    'text': True,
                    'encoding': 'utf-8',
                    'errors': 'replace',
                    'cwd': config.working_dir if config.command_type == "node" else None,
                    'env': {**os.environ, 'MPLCONFIGDIR': '/tmp/matplotlib_cache'}
                }
                
                if use_shell:
                    popen_kwargs['shell'] = True
                popen_kwargs['args'] = cmd
                if not use_shell and sys.platform == 'win32':
                    popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                
                process = subprocess.Popen(**popen_kwargs)

                config.process = process
                config.pid = process.pid
                config.status = "running"

                time.sleep(2)
                if process.poll() is not None:
                    error_msg = "进程立即退出，请检查日志文件"
                    try:
                        with open(service_log_file, 'r', encoding='utf-8') as f:
                            log_content = f.read()
                            if log_content:
                                error_msg = log_content[-1000:]
                    except:
                        pass
                    config.status = "failed"
                    config.error_message = error_msg
                    self.logger.error(f"[{service_name}] 启动失败: {error_msg}")
                    self._log_event(service_name, "FAILED", error_msg)
                    return config

                elapsed = (datetime.now() - config.start_time).total_seconds()
                self.logger.info(
                    f"[{service_name}] 启动成功 - PID: {config.pid}, Port: {config.port}, 耗时: {elapsed:.2f}s"
                )
                self.logger.info(f"[{service_name}] 日志文件: {service_log_file}")
                self._log_event(service_name, "RUNNING", f"PID: {config.pid}, Port: {config.port}, Log: {service_log_file}")

                config.log_file = str(service_log_file)

                self._start_output_monitor(config)

        except FileNotFoundError as e:
            config.status = "failed"
            config.error_message = f"命令未找到，请确保已安装 Node.js/pnpm: {str(e)}"
            self.logger.error(f"[{service_name}] 启动失败: {config.error_message}")
            self._log_event(service_name, "COMMAND_NOT_FOUND", config.error_message)
        except Exception as e:
            config.status = "failed"
            config.error_message = str(e)
            self.logger.error(f"[{service_name}] 启动异常: {str(e)}")
            self._log_event(service_name, "EXCEPTION", str(e))

        return config

    def _validate_node_service(self, config: ServiceConfig) -> Tuple[bool, str]:
        """验证Node.js服务配置"""
        if not config.working_dir:
            return False, "Node.js服务未指定工作目录"

        working_path = Path(config.working_dir)
        if not working_path.exists():
            return False, f"工作目录不存在: {config.working_dir}"

        if not working_path.is_dir():
            return False, f"工作目录路径不是目录: {config.working_dir}"

        package_json = working_path / "package.json"
        if not package_json.exists():
            return False, f"package.json不存在: {package_json}"

        lock_files = ["pnpm-lock.yaml", "package-lock.json", "yarn.lock"]
        has_lock_file = any((working_path / lock).exists() for lock in lock_files)
        if not has_lock_file:
            self.logger.warning(
                f"[{config.display_name}] 未检测到锁文件，可能需要先运行 pnpm install"
            )

        if not config.startup_command:
            return False, "Node.js服务未指定启动命令"

        return True, ""

    def _start_output_monitor(self, config: ServiceConfig):
        """启动输出监控线程"""
        def monitor_process():
            if not config.process:
                return

            try:
                while config.process.poll() is None and not self.shutdown_event.is_set():
                    time.sleep(2)
            except Exception as e:
                self.logger.debug(f"[{config.display_name}] 进程监控结束: {e}")

        monitor_thread = threading.Thread(target=monitor_process, daemon=True)
        monitor_thread.start()

    def start_all_services(self) -> bool:
        """启动所有服务"""
        self.logger.info("=" * 60)
        self.logger.info("Teacher Assistant AI 服务启动管理器")
        self.logger.info("=" * 60)
        self.logger.info(f"启动模式: {'顺序' if self.sequential else '并行'}")
        self.logger.info(f"日志级别: {logging.getLevelName(self.log_level)}")
        self.logger.info("-" * 60)

        overall_start = datetime.now()

        if self.sequential:
            for config in self.services.values():
                self._start_single_service(config)
                time.sleep(1)
        else:
            with ThreadPoolExecutor(max_workers=len(self.services)) as executor:
                futures = {
                    executor.submit(self._start_single_service, config): config.name
                    for config in self.services.values()
                }

                for future in as_completed(futures):
                    service_name = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"[{service_name}] 线程执行异常: {e}")

        elapsed = (datetime.now() - overall_start).total_seconds()
        running_count = sum(1 for s in self.services.values() if s.status == "running")
        failed_count = sum(1 for s in self.services.values() if s.status == "failed")

        self.logger.info("-" * 60)
        self.logger.info(f"启动完成 - 总计: {len(self.services)} 个服务")
        self.logger.info(f"  成功: {running_count} 个")
        self.logger.info(f"  失败: {failed_count} 个")
        self.logger.info(f"  总耗时: {elapsed:.2f} 秒")
        self.logger.info("-" * 60)

        self._print_service_table()

        self._save_startup_report()

        return failed_count == 0

    def _print_service_table(self):
        """打印服务状态表格"""
        self.logger.info("服务状态详情:")
        self.logger.info(f"{'服务名称':<20} {'端口':<8} {'PID':<10} {'状态':<10}")
        self.logger.info("-" * 60)

        for config in self.services.values():
            status_icon = "✓" if config.status == "running" else "✗"
            pid_str = str(config.pid) if config.pid else "N/A"
            self.logger.info(
                f"{config.display_name:<18} {config.port:<8} {pid_str:<10} {status_icon} {config.status}"
            )

            if config.log_file and config.status == "running":
                self.logger.info(f"  日志: {config.log_file}")
            if config.error_message:
                self.logger.info(f"  错误: {config.error_message}")

    def _save_startup_report(self):
        """保存启动报告到文件"""
        report_path = Path(__file__).parent / "logs" / "latest_startup_report.txt"

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("Teacher Assistant AI 启动报告\n")
                f.write("=" * 60 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Python版本: {sys.version}\n")
                f.write("-" * 60 + "\n\n")

                f.write("服务状态:\n")
                f.write(f"{'服务名称':<20} {'端口':<8} {'PID':<10} {'状态':<10} {'日志文件'}\n")
                f.write("-" * 80 + "\n")

                for config in self.services.values():
                    time_str = config.start_time.strftime('%H:%M:%S') if config.start_time else "N/A"
                    pid_str = str(config.pid) if config.pid else "N/A"
                    log_str = config.log_file if config.log_file else "N/A"
                    f.write(
                        f"{config.display_name:<18} {config.port:<8} {pid_str:<10} "
                        f"{config.status:<10} {log_str}\n"
                    )

                f.write("\n" + "-" * 60 + "\n")
                f.write("详细日志:\n")
                for log in self.logs:
                    f.write(
                        f"[{log.timestamp.strftime('%H:%M:%S')}] "
                        f"[{log.service_name}] {log.event}: {log.details}\n"
                    )

            self.logger.info(f"启动报告已保存: {report_path}")
        except Exception as e:
            self.logger.warning(f"保存启动报告失败: {e}")

    def stop_all_services(self):
        """停止所有服务"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("正在停止所有服务...")
        self.logger.info("-" * 60)

        for config in self.services.values():
            if config.process and config.process.poll() is None:
                try:
                    self.logger.info(f"[{config.display_name}] 停止中 (PID: {config.pid})...")

                    if sys.platform == 'win32':
                        subprocess.run(
                            ['taskkill', '/F', '/T', '/PID', str(config.pid)],
                            capture_output=True,
                            check=False
                        )
                    else:
                        config.process.terminate()
                        config.process.wait(timeout=5)

                    config.status = "stopped"
                    self._log_event(config.display_name, "STOPPED", f"PID: {config.pid}")
                    self.logger.info(f"[{config.display_name}] 已停止")

                except Exception as e:
                    self.logger.error(f"[{config.display_name}] 停止失败: {e}")
                    try:
                        config.process.kill()
                    except:
                        pass

        self.logger.info("=" * 60)

    def monitor_services(self):
        """监控服务运行状态"""
        self.logger.info("\n正在监控服务状态 (按 Ctrl+C 停止)...\n")

        try:
            while not self.shutdown_event.is_set():
                for config in self.services.values():
                    if config.process and config.process.poll() is not None:
                        if config.status == "running":
                            config.status = "crashed"
                            self.logger.warning(
                                f"[{config.display_name}] 服务异常退出 (退出码: {config.process.returncode})"
                            )

                time.sleep(5)
        except KeyboardInterrupt:
            pass


def print_help():
    """打印帮助信息"""
    help_text = """
╔══════════════════════════════════════════════════════════════════╗
║         Teacher Assistant AI - 统一服务启动脚本                   ║
╚══════════════════════════════════════════════════════════════════╝

用法:
    python main.py [选项]

选项:
    -h, --help            显示此帮助信息
    -l, --log-level       设置日志级别 (DEBUG/INFO/WARNING/ERROR)
                          默认: INFO
    -s, --sequential      使用顺序启动模式（默认并行启动）
    -v, --version         显示版本信息

示例:
    python main.py                    # 以默认设置启动所有服务
    python main.py --log-level DEBUG  # 启用调试日志
    python main.py --sequential       # 顺序启动服务

服务列表:
    ┌────────────────────┬──────────┬─────────────────────────────┐
    │ 服务名称           │ 端口     │ 描述                        │
    ├────────────────────┼──────────┼─────────────────────────────┤
    │ 登录服务           │ 5000     │ 用户登录/注册(MongoDB)      │
    │ OpenMAIC智能课堂   │ 5006     │ AI通识教育一站式实践平台    │
    │ API统一管理服务    │ 5010     │ API密钥统一管理             │
    │ 手写数字识别服务   │ 5005     │ GPU加速数字识别             │
    │ 练习反馈服务       │ 5011     │ 练习结果反馈与评估          │
    │ 讨论区服务         │ 5020     │ 用户交流讨论区              │
    │ 多方式认证服务     │ 5021     │ 手机号/微信/QQ/邮箱注册登录 │
    └────────────────────┴──────────┴─────────────────────────────┘

控制:
    Ctrl+C                优雅关闭所有服务

日志:
    日志文件保存在 backend/logs/ 目录下
    """
    print(help_text)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Teacher Assistant AI - 统一服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python main.py                    # 启动所有服务
    python main.py -l DEBUG           # 启用调试日志
    python main.py -s                 # 顺序启动
        """
    )

    parser.add_argument(
        '-l', '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='设置日志级别 (默认: INFO)'
    )

    parser.add_argument(
        '-s', '--sequential',
        action='store_true',
        help='使用顺序启动模式（默认并行启动）'
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    args = parser.parse_args()

    launcher = ServiceLauncher(
        log_level=args.log_level,
        sequential=args.sequential
    )

    success = launcher.start_all_services()

    if not success:
        launcher.logger.warning("部分服务启动失败，请检查日志")

    launcher.monitor_services()

    launcher.stop_all_services()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())