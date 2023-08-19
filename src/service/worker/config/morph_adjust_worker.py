import os

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.usecase.config.morph_adjust_usecase import MorphAdjustUsecase
from service.worker.save_worker import SaveWorker

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MorphAdjustWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)
        self.panel = panel

    def thread_execute(self):
        model: PmxModel = self.panel.model_ctrl.data
        motion: VmdMotion = self.panel.motion_ctrl.data

        logger.info("モーフ条件調整開始", decoration=MLogger.Decoration.BOX)

        conditions: list[dict[str, str]] = []
        for condition in self.panel.conditions:
            history = condition.history
            if history:
                conditions.append(history)

        output_motion, fnos = MorphAdjustUsecase().adjust(
            model,
            motion,
            self.panel.output_motion_ctrl.path,
            conditions,
        )

        self.result_data = motion, output_motion, fnos

        SaveWorker(self.frame, self.panel, self.result_func).execute_sub(model.name, output_motion)

        logger.info("モーフ条件調整完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(self.panel.output_motion_ctrl.path)}_morph_adjust.log")
        # 出力されたメッセージを全部出力
        self.panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
