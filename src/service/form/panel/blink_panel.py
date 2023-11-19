import os
from typing import Iterable, Optional

import wx
from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.service_canvas_panel import ServiceCanvasPanel
from service.form.widgets.blink_ctrl_set import BlinkCtrlSet
from service.form.widgets.morph_ctrl_set import MorphCtrlSet
from service.worker.config.blink_worker import BlinkWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class BlinkPanel(ServiceCanvasPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)

    @property
    def emotion_type(self) -> str:
        return "まばたき"

    @property
    def console_rows(self) -> int:
        return 100

    @property
    def key_names(self) -> Iterable[str]:
        return ("まばたき",)

    def create_service_worker(self) -> BlinkWorker:
        return BlinkWorker(self, self.on_exec_result)

    def _initialize_service_ui(self) -> None:
        # --------------
        # まばたき作成

        self.blink_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.blink_title_ctrl = wx.StaticText(
            self.window,
            wx.ID_ANY,
            __("まばたき生成パラメーター: "),
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.blink_title_ctrl.SetToolTip(
            "\n".join(
                [
                    __("頭などの動きに合わせてをまばたきを生成します"),
                    __("まばたき・下モーフを使用しますが、モデルに該当モーフがなく他で代用できる場合は置き換えてください"),
                ]
            )
        )
        self.blink_sizer.Add(self.blink_title_ctrl, 0, wx.ALL, 3)

        self.blink_set = BlinkCtrlSet(self, self.window)
        self.blink_set.initialize({})
        self.blink_sizer.Add(self.blink_set.sizer, 0, wx.ALL, 3)
        self.window_sizer.Add(self.blink_sizer, 0, wx.ALL, 3)

        self.replace_set = MorphCtrlSet(self.frame, self, self.window)
        self.replace_set.initialize([])
        self.window_sizer.Add(self.replace_set.sizer, 0, wx.ALL, 3)

    def Enable(self, enable: bool):
        super().Enable(enable)
        self.blink_set.Enable(enable)
        self.replace_set.Enable(enable)

    def on_preparer_result(
        self,
        result: bool,
        data: Optional[
            tuple[PmxModel, PmxModel, VmdMotion, VmdMotion, dict[str, float]]
        ],
        elapsed_time: str,
    ):
        super().on_preparer_result(result, data, elapsed_time)

        if not (result and data):
            return

        _, model, _, _, blink_conditions = data

        # まばたき条件の初期化
        self.blink_set.initialize(blink_conditions)
        # モーフ置換の初期化
        self.replace_set.initialize(model.morphs)

    def on_show_morph_sub_window(self, event: wx.Event) -> None:
        self.frame.show_morph_sub_window(event, self)
