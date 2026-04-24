'''
Author: Be1k0
URL: https://github.com/Be1k0/YuQue-BdT
'''

import asyncio
import os
import functools
from typing import Dict, List, Optional
from PyQt6.QtCore import pyqtSignal
from gui.controllers.base_controller import BaseController
from src.core.scheduler import Scheduler
from src.libs.constants import MutualAnswer
from src.libs.markdown_asset_localizer import MarkdownAssetLocalizer
from src.libs.tools import get_local_cookies, has_login_cookie

class ExportController(BaseController):
    """导出控制器
    
    负责处理知识库导出和 Markdown 文档资源离线化任务。
    继承自 BaseController ，支持信号机制。
    """
    
    # 信号定义
    export_progress = pyqtSignal(str)    # 导出进度
    image_download_progress = pyqtSignal(int, int, str)  # 资源处理进度
    image_download_finished = pyqtSignal(int, int)   # 资源处理完成
    image_download_error = pyqtSignal(str)   # 资源处理错误
    
    def __init__(self, client=None):
        super().__init__()
        self.client = client 
        self.last_asset_summary: Dict[str, int] = {}
        
    async def export_books(self, answer: MutualAnswer):
        """执行导出任务
        
        Args:
            answer: 导出配置对象
        """
        # 设置进度回调
        answer.progress_callback = self.export_progress.emit
        
        # 创建调度器并开始任务
        scheduler = Scheduler(self.client)
        await scheduler.start_download_task(answer)
        
    async def download_images(
        self,
        md_files: List[str],
        download_threads: int,
        doc_image_prefix: str,
        image_rename_mode: str,
        image_file_prefix: str,
        yuque_cdn_domain: str,
        markdown_meta: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """处理 Markdown 文档中的资源链接
        
        Args:
            md_files: Markdown文件列表
            download_threads: 线程数
            doc_image_prefix: 兼容旧参数，当前未使用
            image_rename_mode: 图片重命名模式
            image_file_prefix: 图片文件前缀
            yuque_cdn_domain: 语雀CDN域名
            markdown_meta: Markdown 文件对应的文档元数据
        """
        try:
            loop = asyncio.get_event_loop()
            cookie_string = get_local_cookies()
            login_ready = has_login_cookie(cookie_string)
            total_assets = 0
            processed_files = 0
            current_filename = ""
            total_direct = 0
            total_card = 0
            total_failed = 0
            total_unsupported = 0
            total_login_required = 0

            self.last_asset_summary = {
                "localized": 0,
                "direct": 0,
                "card": 0,
                "failed": 0,
                "unsupported": 0,
                "login_required": 0,
            }
            
            for md_file in md_files:
                current_filename = os.path.basename(md_file)

                def on_localizer_progress(processed, total):
                    self.image_download_progress.emit(processed, total, current_filename)

                localizer = MarkdownAssetLocalizer(
                    cookie_string=cookie_string,
                    max_workers=download_threads,
                    progress_callback=on_localizer_progress,
                    image_rename_mode=image_rename_mode,
                    image_file_prefix=image_file_prefix,
                    yuque_cdn_domain=yuque_cdn_domain,
                )

                func = functools.partial(
                    localizer.process_single_file,
                    md_file_path=md_file,
                    current_doc_meta=(markdown_meta or {}).get(md_file),
                    has_login_cookie=login_ready,
                )
                stats = await loop.run_in_executor(None, func)
                total_assets += stats.localized_count
                processed_files += 1
                total_direct += stats.direct_count
                total_card += stats.card_count
                total_failed += stats.failed_count
                total_unsupported += stats.unsupported_count
                total_login_required += stats.login_required_count

            self.last_asset_summary = {
                "localized": total_assets,
                "direct": total_direct,
                "card": total_card,
                "failed": total_failed,
                "unsupported": total_unsupported,
                "login_required": total_login_required,
            }
            self.log_info(
                f"文档资源处理完成: 文件 {processed_files} 个, 直接资源 {total_direct}, "
                f"卡片媒体 {total_card}, 需登录 {total_login_required}, "
                f"暂不支持 {total_unsupported}, 失败 {total_failed}"
            )
            self.image_download_finished.emit(processed_files, total_assets)
            
        except Exception as e:
            self.log_error(f"文档资源处理过程出错: {e}")
            self.image_download_error.emit(str(e))
