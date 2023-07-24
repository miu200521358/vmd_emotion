import os
from typing import Optional

import wx

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.file_panel import FilePanel
from service.usecase.load_usecase import LoadUsecase

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)

    def thread_execute(self):
        file_panel: FilePanel = self.frame.file_panel
        model: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None

        is_model_change = False
        usecase = LoadUsecase()

        if file_panel.model_ctrl.valid() and not file_panel.model_ctrl.data:
            logger.info("人物: 読み込み開始", decoration=MLogger.Decoration.BOX)

            original_model = file_panel.model_ctrl.reader.read_by_filepath(file_panel.model_ctrl.path)

            usecase.valid_model(original_model)

            model = original_model.copy()

            is_model_change = True
        elif file_panel.model_ctrl.original_data:
            original_model = file_panel.model_ctrl.original_data
            model = file_panel.model_ctrl.data
        else:
            original_model = PmxModel()
            model = PmxModel()

        if file_panel.motion_ctrl.valid() and (not file_panel.motion_ctrl.data or is_model_change):
            logger.info("モーション読み込み開始", decoration=MLogger.Decoration.BOX)

            original_motion = file_panel.motion_ctrl.reader.read_by_filepath(file_panel.motion_ctrl.path)

            motion = usecase.valid_motion(original_motion)
        elif file_panel.motion_ctrl.original_data:
            motion = file_panel.motion_ctrl.original_data
        else:
            motion = VmdMotion("empty")

        blink_conditions = usecase.get_blink_conditions()

        self.result_data = (original_model, model, original_motion, motion, blink_conditions)

    def output_log(self):
        file_panel: FilePanel = self.frame.file_panel
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(file_panel.output_motion_ctrl.path)}_load.log")
        # 出力されたメッセージを全部出力
        file_panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
