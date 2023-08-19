import os

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.usecase.config.gaze_usecase import GazeUsecase
from service.worker.save_worker import SaveWorker

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class GazeWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)
        self.panel = panel

    def thread_execute(self):
        model: PmxModel = self.panel.model_ctrl.data
        motion: VmdMotion = self.panel.motion_ctrl.data

        logger.info("目線生成開始", decoration=MLogger.Decoration.BOX)

        output_motion, fnos = GazeUsecase().create_gaze(
            model,
            motion,
            self.panel.output_motion_ctrl.path,
            self.panel.gaze_infection_ctrl.GetValue(),
            self.panel.gaze_ratio_x_ctrl.GetValue(),
            self.panel.gaze_limit_upper_x_ctrl.GetValue(),
            self.panel.gaze_limit_lower_x_ctrl.GetValue(),
            self.panel.gaze_ratio_y_ctrl.GetValue(),
            self.panel.gaze_limit_upper_y_ctrl.GetValue(),
            self.panel.gaze_limit_lower_y_ctrl.GetValue(),
            self.panel.gaze_reset_ctrl.GetValue(),
            self.panel.gaze_blink_ctrl.GetValue(),
        )

        self.result_data = motion, output_motion, fnos

        SaveWorker(self.frame, self.panel, self.result_func).execute_sub(model.name, output_motion)

        logger.info("目線生成完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(self.panel.output_motion_ctrl.path)}_gaze.log")
        # 出力されたメッセージを全部出力
        self.panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
