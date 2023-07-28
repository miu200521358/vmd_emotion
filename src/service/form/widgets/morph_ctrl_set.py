import os

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_panel import BasePanel
from service.usecase.load_usecase import DuplicateMorph
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow) -> None:
        self.parent = parent
        self.window = window

        self.morph_duplicate_choices: dict[tuple[int, int], DuplicateMorph] = {}

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.choice_left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.choice_left_btn_ctrl.SetToolTip(__("モーフ組み合わせプルダウンの選択肢を上方向に移動できます。"))
        self.choice_left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_left)
        self.sizer.Add(self.choice_left_btn_ctrl, 0, wx.ALL, 3)

        self.morph_choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(200, -1),
            choices=[],
        )
        self.morph_choice_ctrl.SetToolTip(__("破綻する危険性があるモーフと変化量の組み合わせ"))
        self.morph_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_morph)
        self.sizer.Add(self.morph_choice_ctrl, 0, wx.ALL, 3)

        self.choice_right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.choice_right_btn_ctrl.SetToolTip(__("モーフ組み合わせプルダウンの選択肢を下方向に移動できます。"))
        self.choice_right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_right)
        self.sizer.Add(self.choice_right_btn_ctrl, 0, wx.ALL, 3)

        # -----------
        self.ratio_left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.ratio_left_btn_ctrl.SetToolTip(__("変化量組み合わせプルダウンの選択肢を上方向に移動できます。"))
        self.ratio_left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_ratio_left)
        self.sizer.Add(self.ratio_left_btn_ctrl, 0, wx.ALL, 3)

        self.morph_ratio_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(300, -1),
            choices=[],
        )
        self.morph_ratio_ctrl.SetToolTip(__("モーフ変化量の組み合わせ"))
        self.morph_ratio_ctrl.Bind(wx.EVT_CHOICE, self.on_change_morph_ratio)
        self.sizer.Add(self.morph_ratio_ctrl, 0, wx.ALL, 3)

        self.ratio_right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.ratio_right_btn_ctrl.SetToolTip(__("モーフ組み合わせプルダウンの選択肢を下方向に移動できます。"))
        self.ratio_right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_morph_ratio_right)
        self.sizer.Add(self.ratio_right_btn_ctrl, 0, wx.ALL, 3)

        bone_weight_tooltip = __("このチェックをONにすると、選択されている2つのモーフで重複している頂点範囲を表示します")
        self.bone_weight_check_ctrl = wx.CheckBox(self.window, wx.ID_ANY, __("重複頂点表示"), wx.Point(20, -1), wx.DefaultSize, 0)
        self.bone_weight_check_ctrl.Bind(wx.EVT_CHECKBOX, self.on_show_bone_weight)
        self.bone_weight_check_ctrl.SetToolTip(bone_weight_tooltip)
        self.sizer.Add(self.bone_weight_check_ctrl, 0, wx.ALL, 3)

    def initialize(self, morph_duplicate_choices: dict[tuple[int, int], DuplicateMorph]) -> None:
        self.morph_duplicate_choices = morph_duplicate_choices
        self.morph_choice_ctrl.Clear()
        self.morph_choice_ctrl.AppendItems([morph_choice.choice_name for morph_choice in morph_duplicate_choices.values()])
        self.morph_choice_ctrl.SetSelection(0)
        self.on_change_morph(wx.EVT_CHOICE)

    def on_change_morph(self, event: wx.Event) -> None:
        choice_index = self.morph_choice_ctrl.GetSelection()
        choice_morph = self.morph_duplicate_choices[list(self.morph_duplicate_choices.keys())[choice_index]]
        self.morph_ratio_ctrl.Clear()
        for morph1_ratio, morph2_ratio in choice_morph.ratios:
            self.morph_ratio_ctrl.Append(
                f"[{choice_morph.morph1_name}]({morph1_ratio:.1f}) - [{choice_morph.morph2_name}]({morph2_ratio:.1f})"
            )
        self.morph_ratio_ctrl.SetSelection(0)
        self.on_change_morph_ratio(event)

    def on_change_morph_ratio(self, event: wx.Event) -> None:
        choice_index = self.morph_choice_ctrl.GetSelection()
        choice_morph = self.morph_duplicate_choices[list(self.morph_duplicate_choices.keys())[choice_index]]
        choice_ratio_index = self.morph_ratio_ctrl.GetSelection()
        choice_ratio1, choice_ratio2 = choice_morph.ratios[choice_ratio_index]

        motion = VmdMotion()
        motion.morphs[choice_morph.morph1_name].append(VmdMorphFrame(0, choice_morph.morph1_name, choice_ratio1))
        motion.morphs[choice_morph.morph2_name].append(VmdMorphFrame(0, choice_morph.morph2_name, choice_ratio2))
        self.parent.canvas.model_sets[0].motion = motion
        self.parent.canvas.change_motion(event, model_index=0)

    def on_change_morph_ratio_right(self, event: wx.Event) -> None:
        selection = self.morph_ratio_ctrl.GetSelection()
        if selection == len(self.morph_duplicate_choices) - 1:
            selection = -1
        self.morph_ratio_ctrl.SetSelection(selection + 1)
        self.on_change_morph_ratio(event)

    def on_change_morph_ratio_left(self, event: wx.Event) -> None:
        selection = self.morph_ratio_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.morph_duplicate_choices)
        self.morph_ratio_ctrl.SetSelection(selection - 1)
        self.on_change_morph_ratio(event)

    def on_change_morph_right(self, event: wx.Event) -> None:
        selection = self.morph_choice_ctrl.GetSelection()
        if selection == len(self.morph_duplicate_choices) - 1:
            selection = -1
        self.morph_choice_ctrl.SetSelection(selection + 1)
        self.on_change_morph(event)

    def on_change_morph_left(self, event: wx.Event) -> None:
        selection = self.morph_choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.morph_duplicate_choices)
        self.morph_choice_ctrl.SetSelection(selection - 1)
        self.on_change_morph(event)

    def on_show_bone_weight(self, event: wx.Event) -> None:
        self.parent.Enable(False)
        # ボーンハイライトを変更
        self.parent.show_bone_weight(self.bone_weight_check_ctrl.GetValue())
        self.parent.Enable(True)

    def Enable(self, enable: bool) -> None:
        self.morph_choice_ctrl.Enable(enable)
        self.choice_left_btn_ctrl.Enable(enable)
        self.choice_right_btn_ctrl.Enable(enable)
        self.morph_ratio_ctrl.Enable(enable)
        self.bone_weight_check_ctrl.Enable(enable)
