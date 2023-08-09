import os
from typing import Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.utils.file_utils import get_root_dir
from mlib.vmd.vmd_collection import VmdMotion
from service.usecase.load_usecase import LoadUsecase

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadWorker(BaseWorker):
    def __init__(self, frame: NotebookFrame, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)
        self.panel = panel

    def thread_execute(self):
        model: Optional[PmxModel] = None
        motion: Optional[VmdMotion] = None

        is_model_change = False
        usecase = LoadUsecase()

        if self.panel.model_ctrl.valid() and not self.panel.model_ctrl.data:
            logger.info("人物: 読み込み開始", decoration=MLogger.Decoration.BOX)

            digest = self.panel.model_ctrl.reader.read_hash_by_filepath(self.panel.model_ctrl.path)
            original_model = self.frame.models.get(digest)

            if original_model:
                logger.info("人物: キャッシュ読み込み完了")
            else:
                original_model = self.panel.model_ctrl.reader.read_by_filepath(self.panel.model_ctrl.path)

            model = usecase.valid_model(original_model)

            is_model_change = True
        elif self.panel.model_ctrl.original_data:
            original_model = self.panel.model_ctrl.original_data
            model = self.panel.model_ctrl.data
        else:
            original_model = PmxModel()
            model = PmxModel()

        if self.panel.motion_ctrl.valid() and (not self.panel.motion_ctrl.data or is_model_change):
            logger.info("モーション読み込み開始", decoration=MLogger.Decoration.BOX)

            digest = self.panel.motion_ctrl.reader.read_hash_by_filepath(self.panel.motion_ctrl.path)
            original_motion = self.frame.motions.get(digest)

            if original_motion:
                logger.info("モーション: キャッシュ読み込み完了")
            else:
                original_motion = self.panel.motion_ctrl.reader.read_by_filepath(self.panel.motion_ctrl.path)

            motion = usecase.valid_motion(original_motion)
        elif self.panel.motion_ctrl.original_data:
            motion = self.panel.motion_ctrl.original_data
        else:
            motion = VmdMotion("empty")

        blink_conditions = usecase.get_blink_conditions()

        bone_matrixes = usecase.get_bone_matrixes(model)

        self.result_data = (
            original_model,
            model,
            original_motion,
            motion,
            blink_conditions,
            bone_matrixes,
        )

    def output_log(self):
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(self.panel.output_motion_ctrl.path)}_load.log")
        # 出力されたメッセージを全部出力
        self.panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
