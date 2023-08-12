import os
from typing import Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.image_btn_ctrl import ImageButton
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl, WheelSpinCtrlDouble

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MorphConditionCtrl:
    def __init__(
        self,
        frame: BaseFrame,
        panel: BasePanel,
        window: wx.ScrolledWindow,
        sizer: wx.Sizer,
        model: PmxModel,
        idx: int,
    ) -> None:
        self.frame = frame
        self.panel = panel
        self.window = window
        self.sizer = sizer
        self.model = model
        self.idx = idx

        self.morph_name_ctrl = wx.ComboBox(
            self.window, id=wx.ID_ANY, choices=model.morphs.names, size=wx.Size(150, -1), style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
        )
        self.morph_name_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_enter_choice)
        if 0 < len(model.morphs.names):
            self.morph_name_ctrl.SetSelection(0)
        self.sizer.Add(self.morph_name_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(wx.StaticText(self.window, wx.ID_ANY, " | ", wx.DefaultPosition, wx.DefaultSize, 0), 0, wx.ALL, 3)

        # 下限値
        self.min_title = wx.StaticText(self.window, wx.ID_ANY, __("下限値: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.min_title, 0, wx.ALL, 3)
        self.min_ctrl = WheelSpinCtrlDouble(self.window, initial=-0.1, min=-100.0, max=100.0, inc=0.01, size=wx.Size(60, -1))
        self.sizer.Add(self.min_ctrl, 0, wx.ALL, 3)

        # 上限値
        self.max_title = wx.StaticText(self.window, wx.ID_ANY, __("上限値: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.max_title, 0, wx.ALL, 3)
        self.max_ctrl = WheelSpinCtrlDouble(self.window, initial=1.1, min=-100.0, max=100.0, inc=0.01, size=wx.Size(60, -1))
        self.sizer.Add(self.max_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(wx.StaticText(self.window, wx.ID_ANY, " | ", wx.DefaultPosition, wx.DefaultSize, 0), 0, wx.ALL, 3)

        self.bezier_title = wx.StaticText(self.window, wx.ID_ANY, __("補間曲線: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.bezier_title, 0, wx.ALL, 3)

        # 開始X
        self.start_x_title = wx.StaticText(self.window, wx.ID_ANY, __("開始X: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.start_x_title, 0, wx.ALL, 3)
        self.start_x_ctrl = WheelSpinCtrl(self.window, initial=70, min=0, max=127, size=wx.Size(60, -1))
        self.sizer.Add(self.start_x_ctrl, 0, wx.ALL, 3)

        # 開始Y
        self.start_y_title = wx.StaticText(self.window, wx.ID_ANY, __("開始Y: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.start_y_title, 0, wx.ALL, 3)
        self.start_y_ctrl = WheelSpinCtrl(self.window, initial=10, min=0, max=127, size=wx.Size(60, -1))
        self.sizer.Add(self.start_y_ctrl, 0, wx.ALL, 3)

        # 終了X
        self.end_x_title = wx.StaticText(self.window, wx.ID_ANY, __("終了X: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.end_x_title, 0, wx.ALL, 3)
        self.end_x_ctrl = WheelSpinCtrl(self.window, initial=57, min=0, max=127, size=wx.Size(60, -1))
        self.sizer.Add(self.end_x_ctrl, 0, wx.ALL, 3)

        # 終了Y
        self.end_y_title = wx.StaticText(self.window, wx.ID_ANY, __("終了Y: "), wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.end_y_title, 0, wx.ALL, 3)
        self.end_y_ctrl = WheelSpinCtrl(self.window, initial=117, min=0, max=127, size=wx.Size(60, -1))
        self.sizer.Add(self.end_y_ctrl, 0, wx.ALL, 3)

        self.history_ctrl = wx.Button(self.window, wx.ID_ANY, __("履歴"), wx.DefaultPosition, wx.Size(80, -1))
        self.history_ctrl.SetToolTip(__("過去に設定したモーフ条件調整を再設定できます"))
        self.history_ctrl.Bind(wx.EVT_BUTTON, self.on_show_histories)
        self.sizer.Add(self.history_ctrl, 0, wx.ALL, 3)

        self.bezier_view_ctrl: ImageButton = ImageButton(
            self.window,
            "resources/icon/visibility_on.png",
            wx.Size(15, 15),
            self.on_show_bezier,
            __("ボタンをONにすると、補間曲線の形や補間曲線に準拠したモーフの変化をプレビューで確認できます"),
        )
        self.sizer.Add(self.bezier_view_ctrl, 0, wx.ALL, 3)

    def on_show_histories(self, event: wx.Event) -> None:
        """履歴一覧を表示する"""
        histories = [
            f'{history["model"]}:{history["morph_name"]} limit[{history["min"]} - {history["max"]}]'
            + f'curve[({history["start_x"]}, {history["start_y"]}), ({history["end_x"]}, {history["end_y"]})]'
            for history in self.frame.histories["morph_condition"]
        ] + [" " * 200]

        with wx.SingleChoiceDialog(
            self.frame,
            __("条件を選んでダブルクリック、またはOKボタンをクリックしてください。"),
            caption=__("モーフ条件調整選択"),
            choices=histories,
            style=wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.OK | wx.CANCEL | wx.CENTRE,
        ) as dialog:
            choiceDialog: wx.SingleChoiceDialog = dialog
            if choiceDialog.ShowModal() == wx.ID_CANCEL:
                return

            idx = choiceDialog.GetSelection()
            history = self.frame.histories["morph_condition"][idx]
            self.start_x_ctrl.SetValue(int(history["start_x"]))
            self.start_y_ctrl.SetValue(int(history["start_y"]))
            self.end_x_ctrl.SetValue(int(history["end_x"]))
            self.end_y_ctrl.SetValue(int(history["end_y"]))
            self.min_ctrl.SetValue(float(history["min"]))
            self.max_ctrl.SetValue(float(history["max"]))

    def Enable(self, enable: bool) -> None:
        self.morph_name_ctrl.Enable(enable)
        self.min_ctrl.Enable(enable)
        self.max_ctrl.Enable(enable)
        self.start_x_ctrl.Enable(enable)
        self.start_y_ctrl.Enable(enable)
        self.end_x_ctrl.Enable(enable)
        self.end_y_ctrl.Enable(enable)
        self.history_ctrl.Enable(enable)
        self.bezier_view_ctrl.Enable(enable)

    def on_enter_choice(self, event: wx.Event) -> None:
        """一致している名前があれば選択"""
        idx = event.GetEventObject().FindString(event.GetEventObject().GetValue())
        if idx >= 0:
            event.GetEventObject().SetSelection(idx)

    def on_show_bezier(self, event: wx.Event) -> None:
        self.frame.show_bezier_dialog(event, self.panel, self)

    @property
    def history(self) -> Optional[dict[str, str]]:
        if not self.morph_name_ctrl.GetStringSelection():
            return None

        return {
            "model": self.model.name,
            "morph_name": str(self.morph_name_ctrl.GetStringSelection()),
            "min": str(self.min_ctrl.GetValue()),
            "max": str(self.max_ctrl.GetValue()),
            "start_x": str(self.start_x_ctrl.GetValue()),
            "start_y": str(self.start_y_ctrl.GetValue()),
            "end_x": str(self.end_x_ctrl.GetValue()),
            "end_y": str(self.end_y_ctrl.GetValue()),
        }
