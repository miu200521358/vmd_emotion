import os

import wx

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.file_panel import FilePanel
from service.usecase.config.gaze_usecase import GazeUsecase

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class GazeWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.frame.file_panel
        model: PmxModel = file_panel.model_ctrl.data
        motion: VmdMotion = file_panel.motion_ctrl.data
        output_motion: VmdMotion = file_panel.output_motion_ctrl.data

        logger.info("目線生成開始", decoration=MLogger.Decoration.BOX)

        GazeUsecase().create_gaze(
            model,
            motion,
            output_motion,
            self.frame.config_panel.gaze_infection_slider.GetValue(),
            self.frame.config_panel.gaze_ratio_x_slider.GetValue(),
            self.frame.config_panel.gaze_ratio_y_slider.GetValue(),
            int(self.frame.config_panel.gaze_reset_slider.GetValue()),
        )

        self.result_data = motion, output_motion

        logger.info("目線生成完了", decoration=MLogger.Decoration.BOX)

    def output_log(self):
        file_panel: FilePanel = self.frame.file_panel
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(file_panel.output_motion_ctrl.path)}_gaze.log")
        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
