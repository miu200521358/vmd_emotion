import os

import wx
from mlib.core.logger import MLogger
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_panel import BasePanel
from mlib.utils.file_utils import get_root_dir
from service.usecase.config.motion_merge_usecase import MotionMergeUsecase
from service.worker.save_worker import SaveWorker

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MotionMergeWorker(BaseWorker):
    def __init__(self, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(panel, result_event)

    def thread_execute(self):
        logger.info("モーション統合開始", decoration=MLogger.Decoration.BOX)

        motion_paths: list[str] = []
        for motion in self.panel.motions:
            if motion.valid():
                motion_paths.append(motion.path)

        output_motion = MotionMergeUsecase().merge(
            motion_paths, self.panel.output_motion_ctrl.path
        )

        fnos: list[int] = []
        self.result_data = motion, output_motion, fnos

        SaveWorker(self.panel, self.result_func).execute_sub("統合データ", output_motion)

        logger.info("モーション統合完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        output_log_path = os.path.join(
            get_root_dir(),
            f"{os.path.basename(self.panel.output_motion_ctrl.path)}_merge.log",
        )
        # 出力されたメッセージを全部出力
        self.panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
