import os

import wx

from mlib.core.exception import MApplicationException
from mlib.core.logger import MLogger
from mlib.service.base_worker import BaseWorker
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.utils.file_utils import get_root_dir
from service.usecase.save_usecase import SaveUsecase

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class SaveWorker(BaseWorker):
    def __init__(self, frame: BaseFrame, panel: BasePanel, result_event: wx.Event) -> None:
        super().__init__(frame, result_event)
        self.panel = panel

    def thread_execute(self):
        if not self.panel.model_ctrl.data:
            raise MApplicationException("モデルデータが読み込まれていません")

        if not self.panel.motion_ctrl.data:
            raise MApplicationException("モーションデータが読み込まれていません")

        if not self.panel.output_motion_ctrl.data:
            raise MApplicationException("出力用モーションデータが生成されていません")

        if not self.panel.output_motion_ctrl.path or not os.path.exists(os.path.dirname(self.panel.output_motion_ctrl.path)):
            logger.warning("出力ファイルパスが有効なパスではないため、デフォルトの出力ファイルパスを再設定します。")
            self.panel.create_output_path()
            os.makedirs(os.path.dirname(self.panel.output_motion_ctrl.path), exist_ok=True)

        logger.info("モーション出力開始", decoration=MLogger.Decoration.BOX)

        SaveUsecase().save(
            self.panel.model_ctrl.data,
            self.panel.output_motion_ctrl.data,
            self.panel.output_motion_ctrl.path,
        )

        logger.info("*** モーション出力成功 ***\n出力先: {f}", f=self.panel.output_motion_ctrl.path, decoration=MLogger.Decoration.BOX)

    def output_log(self):
        output_log_path = os.path.join(get_root_dir(), f"{os.path.basename(self.panel.output_motion_ctrl.path)}_save.log")
        # 出力されたメッセージを全部出力
        self.panel.console_ctrl.text_ctrl.SaveFile(filename=output_log_path)
