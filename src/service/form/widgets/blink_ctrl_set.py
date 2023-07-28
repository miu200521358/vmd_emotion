import os

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrlDouble

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
        self.condition_choice_ctrl.SetToolTip(
            "\n".join(
                [
                    __("まばたきを生成する条件の選択肢\n選択肢ごとに発生確率を設定できます"),
                    __("確率が0より大きい場合、該当条件に合致するキーフレでまばたきを生成します。"),
                ]
            )
        )
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

        condition_probability_tooltip = "\n".join(
            [
                __("まばたきを生成する条件の発生確率。"),
                __("100%の場合、該当する箇所で必ず発生しますが、近隣により上位（順番が上）のまばたきの発生が予定されている場合、そちらを優先します。"),
            ]
        )

        self.condition_probability_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("条件発生確率"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.condition_probability_title_ctrl.SetToolTip(condition_probability_tooltip)
        self.sizer.Add(self.condition_probability_title_ctrl, 0, wx.ALL, 3)

        self.condition_probability_ctrl = WheelSpinCtrl(
            self.window, initial=80, min=0, max=100, size=wx.Size(60, -1), change_event=self.on_change_probability
        )
        self.condition_probability_ctrl.SetToolTip(condition_probability_tooltip)
        self.sizer.Add(self.condition_probability_ctrl, 0, wx.ALL, 3)

        self.zero_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "0",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.zero_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を0%に設定します"))
        self.zero_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_probability_zero)
        self.sizer.Add(self.zero_btn_ctrl, 0, wx.ALL, 3)

        self.half1_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "40",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.half1_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を40%に設定します"))
        self.half1_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_probability_half1)
        self.sizer.Add(self.half1_btn_ctrl, 0, wx.ALL, 3)

        self.half2_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "80",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.half2_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を80%に設定します"))
        self.half2_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_probability_half2)
        self.sizer.Add(self.half2_btn_ctrl, 0, wx.ALL, 3)

        self.full_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "100",
            wx.DefaultPosition,
            wx.Size(35, -1),
        )
        self.full_btn_ctrl.SetToolTip(__("まばたき生成条件の発生確率を100%に設定します"))
        self.full_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_probability_full)
        self.sizer.Add(self.full_btn_ctrl, 0, wx.ALL, 3)

        linkage_depth_tooltip = "\n".join(
            [
                __("まばたきを生成する際の連動部位（眉下・目線下）の変動量"),
                __("値が大きいほど、大きく連動します"),
            ]
        )

        self.linkage_depth_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("連動の深さ"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.linkage_depth_title_ctrl.SetToolTip(linkage_depth_tooltip)
        self.sizer.Add(self.linkage_depth_title_ctrl, 0, wx.ALL, 3)

        self.linkage_depth_ctrl = WheelSpinCtrlDouble(self.window, initial=0.5, min=0, max=1, inc=0.1, size=wx.Size(60, -1))
        self.linkage_depth_ctrl.SetToolTip(linkage_depth_tooltip)
        self.sizer.Add(self.linkage_depth_ctrl, 0, wx.ALL, 3)

        # --------------
        blink_span_tooltip = __("まばたきの間隔\n値が小さいほど、細かくまばたきをします")

        self.blink_span_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("間隔"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.blink_span_title_ctrl.SetToolTip(blink_span_tooltip)
        self.sizer.Add(self.blink_span_title_ctrl, 0, wx.ALL, 3)

        self.blink_span_ctrl = WheelSpinCtrl(self.window, initial=60, min=10, max=150, size=wx.Size(60, -1))
        self.blink_span_ctrl.SetToolTip(blink_span_tooltip)
        self.sizer.Add(self.blink_span_ctrl, 0, wx.ALL, 3)

    def initialize(self, blink_conditions: dict[str, float]) -> None:
        self.condition_choice_ctrl.Clear()
        for condition_name, condition_probability in blink_conditions.items():
            self.condition_choice_ctrl.Append(condition_name)
            self.condition_probabilities[condition_name] = condition_probability
        self.condition_choice_ctrl.SetSelection(0)
        self.condition_probability_ctrl.SetValue(100)

    def on_change_condition(self, event: wx.Event) -> None:
        condition_name = self.condition_choice_ctrl.GetStringSelection()
        self.condition_probability_ctrl.SetValue(self.condition_probabilities[condition_name])

    def on_change_probability_zero(self, event: wx.Event) -> None:
        self.condition_probability_ctrl.SetValue(0)
        self.on_change_probability(event)

    def on_change_probability_half1(self, event: wx.Event) -> None:
        self.condition_probability_ctrl.SetValue(40)
        self.on_change_probability(event)

    def on_change_probability_half2(self, event: wx.Event) -> None:
        self.condition_probability_ctrl.SetValue(80)
        self.on_change_probability(event)

    def on_change_probability_full(self, event: wx.Event) -> None:
        self.condition_probability_ctrl.SetValue(100)
        self.on_change_probability(event)

    def on_change_probability(self, event: wx.Event) -> None:
        condition_name = self.condition_choice_ctrl.GetStringSelection()
        self.condition_probabilities[condition_name] = self.condition_probability_ctrl.GetValue()

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
        self.condition_probability_ctrl.Enable(enable)
        self.zero_btn_ctrl.Enable(enable)
        self.half2_btn_ctrl.Enable(enable)
        self.half1_btn_ctrl.Enable(enable)
        self.full_btn_ctrl.Enable(enable)
        self.linkage_depth_ctrl.Enable(enable)
        self.blink_span_ctrl.Enable(enable)
