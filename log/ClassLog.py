import logging
import os
import queue
import threading
from datetime import datetime, time, timedelta
from logging.handlers import RotatingFileHandler


class Log:
    def __init__(self, log_dir="logs", max_queue_size=10000):
        """
        异步日志记录器
        :param log_dir: 日志存储目录
        :param max_queue_size: 最大队列容量
        """
        # 初始化路径
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(self.log_dir, exist_ok=True)

        # 线程控制
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        # 日志处理器状态
        self.current_date = datetime.now().date()
        self.file_handler = None
        self.console_handler = logging.StreamHandler()

        # 初始化日志系统
        self._init_logger()
        self._start_workers()

    def _init_logger(self):
        """初始化核心logger实例"""
        self.logger = logging.getLogger("AsyncDateLogger")
        self.logger.setLevel(logging.INFO)

        # 控制台处理器
        self.console_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(self.console_handler)

        # 文件处理器
        self._rotate_file_handler()

    def _get_formatter(self):
        """统一的日志格式"""
        return logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def _rotate_file_handler(self):
        """轮转文件处理器（线程安全）"""
        with self.lock:
            # 移除旧处理器
            if self.file_handler:
                self.logger.removeHandler(self.file_handler)
                self.file_handler.close()

            # 创建新文件处理器
            filename = os.path.join(
                self.log_dir,
                f"{datetime.now().strftime('%Y%m%d')}.log"
            )
            self.file_handler = RotatingFileHandler(
                filename,
                encoding='utf-8',
                maxBytes=100 * 1024 * 1024,  # 100MB
                backupCount=7
            )
            self.file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(self.file_handler)

            # 更新日期状态
            self.current_date = datetime.now().date()

    def _start_workers(self):
        """启动后台工作线程"""
        # 日志消费线程
        log_worker = threading.Thread(
            target=self._consume_logs,
            daemon=True
        )
        log_worker.start()

        # 日期检测线程
        date_checker = threading.Thread(
            target=self._watch_date_change,
            daemon=True
        )
        date_checker.start()

    def _watch_date_change(self):
        """精确的日期监控线程"""
        while not self.stop_event.is_set():
            now = datetime.now()
            next_day = now.date() + timedelta(days=1)
            next_check = datetime.combine(next_day, time(0, 0, 0))

            # 计算等待时间
            sleep_seconds = (next_check - now).total_seconds()
            if sleep_seconds > 0:
                self.stop_event.wait(sleep_seconds)

            # 触发日期检查
            if datetime.now().date() != self.current_date:
                self._rotate_file_handler()

    def _consume_logs(self):
        """消费日志队列（核心工作线程）"""
        while not self.stop_event.is_set() or not self.log_queue.empty():
            try:
                record = self.log_queue.get(timeout=1)
                self.logger.handle(record)
                self.log_queue.task_done()
            except queue.Empty:
                continue

    def log(self, message, level="info"):
        """记录日志（线程安全的生产者）"""
        if self.log_queue.full():
            # 队列满时降级处理
            self._handle_queue_full(message)
            return

        log_level = getattr(logging, level.upper(), logging.INFO)
        record = logging.LogRecord(
            name=self.logger.name,
            level=log_level,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=None,
            exc_info=None
        )
        self.log_queue.put(record)

    def _handle_queue_full(self, message):
        """队列溢出处理策略"""
        # 1. 尝试扩容写入
        try:
            self.log_queue.put_nowait(message)
        except queue.Full:
            # 2. 丢弃日志并告警
            print(f"WARNING: Log queue full, dropping message: {message}")

    def shutdown(self):
        """安全关闭日志系统"""
        self.stop_event.set()

        # 等待队列清空
        while not self.log_queue.empty():
            try:
                record = self.log_queue.get_nowait()
                self.logger.handle(record)
                self.log_queue.task_done()
            except queue.Empty:
                break

        # 关闭处理器
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()
        self.logger.removeHandler(self.console_handler)

    def write(self, message, level="info"):
        """
        兼容旧版本的写入方法
        info
        warning
        error
        """

        self.log(message, level)