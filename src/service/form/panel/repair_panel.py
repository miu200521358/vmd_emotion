import os
from typing import Iterable

import wx
from mlib.core.logger import MLogger
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrlDouble
from service.form.panel.service_canvas_panel import ServiceCanvasPanel
from service.worker.config.morph_repair_worker import MorphRepairWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class RepairPanel(ServiceCanvasPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)

    @property
    def emotion_type(self) -> str:
        return "破綻補正モーフ"

    @property
    def console_rows(self) -> int:
        return 170

    @property
    def key_names(self) -> Iterable[str]:
        return []

    def create_service_worker(self) -> MorphRepairWorker:
        return MorphRepairWorker(self, self.on_exec_result)

    def _initialize_service_ui(self) -> None:
        self.repair_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.repair_title_ctrl = wx.StaticText(
            self.window,
            wx.ID_ANY,
            __("破綻補正パラメーター: "),
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.repair_title_ctrl.SetToolTip(
            "\n".join(
                [
                    __("モデルとモーフの組み合わせによって破綻している箇所がある場合、補正します"),
                    __("表情生成後、出力vmdファイル名の末尾にrepairを付けてvmd出力します"),
                    __("補正キーフレだけ出力するため、元となった表情モーションの後に読み込んでください"),
                ]
            )
        )
        self.repair_sizer.Add(self.repair_title_ctrl, 0, wx.ALL, 3)

        # --------------
        check_morph_tooltip = __("チェック対象となるモーフの合計変形量\n値が小さいほど、少しのモーフ変形量でもチェックを行います")

        self.check_morph_title_ctrl = wx.StaticText(
            self.window,
            wx.ID_ANY,
            __("チェック対象変形量"),
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.check_morph_title_ctrl.SetToolTip(check_morph_tooltip)
        self.repair_sizer.Add(self.check_morph_title_ctrl, 0, wx.ALL, 3)

        self.check_morph_threshold_ctrl = WheelSpinCtrlDouble(
            self.window, initial=0.8, min=0.0, max=2.0, inc=0.01, size=wx.Size(60, -1)
        )
        self.check_morph_threshold_ctrl.SetToolTip(check_morph_tooltip)
        self.repair_sizer.Add(self.check_morph_threshold_ctrl, 0, wx.ALL, 3)

        # --------------
        repair_morph_tooltip = __("モーフが破綻している場合の補正係数\n値が小さいほど、補正が強くかかります")

        self.repair_morph_title_ctrl = wx.StaticText(
            self.window,
            wx.ID_ANY,
            __("補正係数"),
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self.repair_morph_title_ctrl.SetToolTip(repair_morph_tooltip)
        self.repair_sizer.Add(self.repair_morph_title_ctrl, 0, wx.ALL, 3)

        self.repair_morph_factor_ctrl = WheelSpinCtrlDouble(
            self.window, initial=1.2, min=1.0, max=2.0, inc=0.01, size=wx.Size(60, -1)
        )
        self.repair_morph_factor_ctrl.SetToolTip(repair_morph_tooltip)
        self.repair_sizer.Add(self.repair_morph_factor_ctrl, 0, wx.ALL, 3)

        # --------------
        self.window_sizer.Add(self.repair_sizer, 0, wx.ALL, 3)

    def Enable(self, enable: bool):
        super().Enable(enable)
        self.check_morph_threshold_ctrl.Enable(enable)
        self.repair_morph_factor_ctrl.Enable(enable)
