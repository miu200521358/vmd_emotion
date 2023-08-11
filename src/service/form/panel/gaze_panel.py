import os
from typing import Iterable

import wx

from mlib.core.logger import MLogger
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl, WheelSpinCtrlDouble
from service.form.panel.service_canvas_panel import ServiceCanvasPanel
from service.worker.config.gaze_worker import GazeWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class GazePanel(ServiceCanvasPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)

    @property
    def emotion_type(self) -> str:
        return "目線"

    @property
    def console_rows(self) -> int:
        return 170

    @property
    def key_names(self) -> Iterable[str]:
        return ("両目",)

    def create_service_worker(self) -> GazeWorker:
        return GazeWorker(self.frame, self, self.on_exec_result)

    def _initialize_service_ui(self) -> None:
        self.gaze_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.gaze_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("目線生成パラメーター: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_title_ctrl.SetToolTip(
            "\n".join(
                [
                    __("頭などの動きに合わせて目線を生成します"),
                    __("両目ボーンを使用します"),
                ]
            )
        )
        self.gaze_sizer.Add(self.gaze_title_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_infection_tooltip = __("目線キーフレを作成する頻度。\n値が大きいほど、小さな動きでも目線が動くようになります。")

        self.gaze_infection_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("頻度"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_infection_title_ctrl.SetToolTip(gaze_infection_tooltip)
        self.gaze_sizer.Add(self.gaze_infection_title_ctrl, 0, wx.ALL, 3)

        self.gaze_infection_ctrl = WheelSpinCtrlDouble(self.window, initial=0.5, min=0.1, max=1.0, inc=0.01, size=wx.Size(55, -1))
        self.gaze_infection_ctrl.SetToolTip(gaze_infection_tooltip)
        self.gaze_sizer.Add(self.gaze_infection_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_ratio_x_tooltip = __("目線キーフレで設定する縦方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_x_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("縦振り幅"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_ratio_x_title_ctrl.SetToolTip(gaze_ratio_x_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_x_ctrl = WheelSpinCtrlDouble(self.window, initial=0.7, min=0.5, max=1.5, inc=0.01, size=wx.Size(55, -1))
        self.gaze_ratio_x_ctrl.SetToolTip(gaze_ratio_x_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_upper_x_tooltip = __("目線キーフレで設定する縦方向の値の上限。\n上限を超えた回転量になった場合、上限までしか動かしません。")

        self.gaze_limit_upper_x_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("縦上限"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_limit_upper_x_title_ctrl.SetToolTip(gaze_limit_upper_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_upper_x_ctrl = WheelSpinCtrl(self.window, initial=3, min=0, max=45, size=wx.Size(50, -1))
        self.gaze_limit_upper_x_ctrl.SetToolTip(gaze_limit_upper_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_lower_x_tooltip = __("目線キーフレで設定する縦方向の値の下限。\n下限を超えた回転量になった場合、下限までしか動かしません。")

        self.gaze_limit_lower_x_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("縦下限"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_limit_lower_x_title_ctrl.SetToolTip(gaze_limit_lower_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_lower_x_ctrl = WheelSpinCtrl(self.window, initial=-7, min=-45, max=0, size=wx.Size(50, -1))
        self.gaze_limit_lower_x_ctrl.SetToolTip(gaze_limit_lower_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_ratio_y_tooltip = __("目線キーフレで設定する横方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_y_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("横振り幅"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_ratio_y_title_ctrl.SetToolTip(gaze_ratio_y_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_y_ctrl = WheelSpinCtrlDouble(self.window, initial=0.7, min=0.5, max=1.5, inc=0.01, size=wx.Size(55, -1))
        self.gaze_ratio_y_ctrl.SetToolTip(gaze_ratio_y_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_upper_y_tooltip = __("目線キーフレで設定する横方向の値の上限（向かって左側）。\n上限を超えた回転量になった場合、上限までしか動かしません。")

        self.gaze_limit_upper_y_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("横上限"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_limit_upper_y_title_ctrl.SetToolTip(gaze_limit_upper_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_upper_y_ctrl = WheelSpinCtrl(self.window, initial=12, min=0, max=45, size=wx.Size(55, -1))
        self.gaze_limit_upper_y_ctrl.SetToolTip(gaze_limit_upper_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_lower_y_tooltip = __("目線キーフレで設定する横方向の値の下限（向かって右側）。\n下限を超えた回転量になった場合、下限までしか動かしません。")

        self.gaze_limit_lower_y_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("横下限"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_limit_lower_y_title_ctrl.SetToolTip(gaze_limit_lower_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_lower_y_ctrl = WheelSpinCtrl(self.window, initial=-12, min=-45, max=0, size=wx.Size(55, -1))
        self.gaze_limit_lower_y_ctrl.SetToolTip(gaze_limit_lower_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_reset_tooltip = __("目線をリセットするキーフレ間隔\n値が小さいほど、目線を細かくリセットします")

        self.gaze_reset_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("リセット"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_reset_title_ctrl.SetToolTip(gaze_reset_tooltip)
        self.gaze_sizer.Add(self.gaze_reset_title_ctrl, 0, wx.ALL, 3)

        self.gaze_reset_ctrl = WheelSpinCtrl(self.window, initial=12, min=5, max=30, size=wx.Size(50, -1))
        self.gaze_reset_ctrl.SetToolTip(gaze_reset_tooltip)
        self.gaze_sizer.Add(self.gaze_reset_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_blink_tooltip = __("目線の上下に合わせたまばたきモーフを追加する際の補正係数")

        self.gaze_blink_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("まばたき係数"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_blink_title_ctrl.SetToolTip(gaze_blink_tooltip)
        self.gaze_sizer.Add(self.gaze_blink_title_ctrl, 0, wx.ALL, 3)

        self.gaze_blink_ctrl = WheelSpinCtrlDouble(self.window, initial=0.2, min=0.0, max=1.0, inc=0.01, size=wx.Size(55, -1))
        self.gaze_blink_ctrl.SetToolTip(gaze_blink_tooltip)
        self.gaze_sizer.Add(self.gaze_blink_ctrl, 0, wx.ALL, 3)

        # --------------
        self.window_sizer.Add(self.gaze_sizer, 0, wx.ALL, 3)

    def Enable(self, enable: bool):
        super().Enable(enable)
        self.gaze_infection_ctrl.Enable(enable)
        self.gaze_ratio_x_ctrl.Enable(enable)
        self.gaze_limit_upper_x_ctrl.Enable(enable)
        self.gaze_limit_lower_x_ctrl.Enable(enable)
        self.gaze_ratio_y_ctrl.Enable(enable)
        self.gaze_limit_upper_y_ctrl.Enable(enable)
        self.gaze_limit_lower_y_ctrl.Enable(enable)
        self.gaze_reset_ctrl.Enable(enable)
        self.gaze_blink_ctrl.Enable(enable)
