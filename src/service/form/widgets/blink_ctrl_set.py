import os

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class BlinkCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow) -> None:
        self.parent = parent
        self.window = window

        self.condition_probabilities: dict[str, float] = {}

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.left_btn_ctrl.SetToolTip(__("条件プルダウンの選択肢を上方向に移動できます。"))
        self.left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_left)
        self.sizer.Add(self.left_btn_ctrl, 0, wx.ALL, 3)

        self.condition_choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(300, -1),
            choices=[],
        )
        self.condition_choice_ctrl.SetToolTip(__("まばたきを生成する条件の選択肢"))
        self.condition_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_condition)
        self.sizer.Add(self.condition_choice_ctrl, 0, wx.ALL, 3)

        self.right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.right_btn_ctrl.SetToolTip(__("条件プルダウンの選択肢を下方向に移動できます。"))
        self.right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_right)
        self.sizer.Add(self.right_btn_ctrl, 0, wx.ALL, 3)

        self.slider = FloatSliderCtrl(
            parent=self.window,
            value=80,
            min_value=0,
            max_value=100,
            increment=1,
            spin_increment=1,
            border=3,
            size=wx.Size(160, -1),
            tooltip=__("まばたきを生成する条件の発生確率"),
        )

        self.sizer.Add(self.slider.sizer, 0, wx.ALL, 3)

        self.zero_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.zero_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を0%に設定します"))
        self.zero_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_zero)
        self.sizer.Add(self.zero_btn_ctrl, 0, wx.ALL, 3)

        self.half1_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "40",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.half1_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を40%に設定します"))
        self.half1_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_half1)
        self.sizer.Add(self.half1_btn_ctrl, 0, wx.ALL, 3)

        self.half2_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "80",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.half2_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を80%に設定します"))
        self.half2_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_half2)
        self.sizer.Add(self.half2_btn_ctrl, 0, wx.ALL, 3)

        self.full_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "100",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.full_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を100%に設定します"))
        self.full_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_condition_full)
        self.sizer.Add(self.full_btn_ctrl, 0, wx.ALL, 3)

    def initialize(self, blink_conditions: dict[str, float]) -> None:
        self.condition_choice_ctrl.Clear()
        for condition_name, condition_probability in blink_conditions.items():
            self.condition_choice_ctrl.Append(condition_name)
            self.condition_probabilities[condition_name] = condition_probability
        self.condition_choice_ctrl.SetSelection(0)
        self.slider.ChangeValue(100)

    def on_change_condition(self, event: wx.Event) -> None:
        condition_name = self.condition_choice_ctrl.GetStringSelection()
        self.slider.ChangeValue(self.condition_probabilities[condition_name])

    def on_change_condition_zero(self, event: wx.Event) -> None:
        self.slider.SetValue(0.0)

    def on_change_condition_half1(self, event: wx.Event) -> None:
        self.slider.SetValue(40.0)

    def on_change_condition_half2(self, event: wx.Event) -> None:
        self.slider.SetValue(80.0)

    def on_change_condition_full(self, event: wx.Event) -> None:
        self.slider.SetValue(100.0)

    def on_change_condition_right(self, event: wx.Event) -> None:
        selection = self.condition_choice_ctrl.GetSelection()
        if selection == len(self.condition_probabilities) - 1:
            selection = -1
        self.condition_choice_ctrl.SetSelection(selection + 1)
        self.on_change_condition(event)

    def on_change_condition_left(self, event: wx.Event) -> None:
        selection = self.condition_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.condition_probabilities)
        self.condition_choice_ctrl.SetSelection(selection - 1)
        self.on_change_condition(event)

    def Enable(self, enable: bool) -> None:
        self.condition_choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.slider.Enable(enable)
        self.zero_btn_ctrl.Enable(enable)
        self.half2_btn_ctrl.Enable(enable)
        self.half1_btn_ctrl.Enable(enable)
        self.full_btn_ctrl.Enable(enable)
