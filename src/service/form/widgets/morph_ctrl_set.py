import os

import wx

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import Morphs
from mlib.pmx.pmx_part import Morph, MorphPanel
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphCtrlSet:
    def __init__(self, parent: BasePanel, window: wx.ScrolledWindow) -> None:
        self.parent = parent
        self.window = window

        self.morphs: Morphs = Morphs()

        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.morph_title_ctrl = wx.StaticText(
            self.window, wx.ID_ANY, __("ツールで生成するモーフ名をモデルに合わせて変更できます"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.sizer.Add(self.morph_title_ctrl, 0, wx.ALL, 3)

        self.sizer.Add(
            wx.StaticLine(self.window, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL), 0, wx.EXPAND | wx.ALL, 5
        )

        self.below_eyebrow_morph_ctrl = MorphReplaceSet(self.parent, self.window)
        self.sizer.Add(self.below_eyebrow_morph_ctrl.sizer, 0, wx.ALL, 3)

        self.blink_morph_ctrl = MorphReplaceSet(self.parent, self.window)
        self.sizer.Add(self.blink_morph_ctrl.sizer, 0, wx.ALL, 3)

        self.laugh_morph_ctrl = MorphReplaceSet(self.parent, self.window)
        self.sizer.Add(self.laugh_morph_ctrl.sizer, 0, wx.ALL, 3)

    def initialize(self, morphs: Morphs) -> None:
        self.morphs = morphs
        self.below_eyebrow_morph_ctrl.initialize("下", __("眉を下に動かす"), morphs.filter_by_panel(MorphPanel.EYEBROW_LOWER_LEFT))
        self.blink_morph_ctrl.initialize("まばたき", __("まばたきをする"), morphs.filter_by_panel(MorphPanel.EYE_UPPER_LEFT))
        self.laugh_morph_ctrl.initialize("笑い", __("笑ったまま目を閉じる"), morphs.filter_by_panel(MorphPanel.EYE_UPPER_LEFT))

    def Enable(self, enable: bool) -> None:
        self.below_eyebrow_morph_ctrl.Enable(enable)


class MorphReplaceSet:
    def __init__(self, parent: BasePanel, window: wx.Window) -> None:
        self.parent = parent
        self.window = window
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.morph_names: list[str] = []

        self.description_ctrl = wx.TextCtrl(
            self.window,
            wx.ID_ANY,
            "",
            wx.DefaultPosition,
            wx.Size(150, -1),
            wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS,
        )
        self.description_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.description_ctrl.SetToolTip(__("生成モーフの内容"))
        self.sizer.Add(self.description_ctrl, 0, wx.ALL, 3)

        self.original_name_ctrl = wx.TextCtrl(
            self.window,
            wx.ID_ANY,
            "",
            wx.DefaultPosition,
            wx.Size(60, -1),
            wx.TE_READONLY | wx.BORDER_NONE | wx.WANTS_CHARS,
        )
        self.original_name_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))
        self.original_name_ctrl.SetToolTip(__("ツール側で生成するモーフ名"))
        self.sizer.Add(self.original_name_ctrl, 0, wx.ALL, 3)

        self.left_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            "<",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.left_btn_ctrl.SetToolTip(__("モーフの選択肢を上方向に移動できます。"))
        self.left_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_left)
        self.sizer.Add(self.left_btn_ctrl, 0, wx.ALL, 3)

        self.choice_ctrl = wx.Choice(
            self.window,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(150, -1),
            choices=[],
        )
        self.choice_ctrl.SetToolTip(__("置き換えモーフの選択肢"))
        self.choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_morph)
        self.sizer.Add(self.choice_ctrl, 0, wx.ALL, 3)

        self.right_btn_ctrl = wx.Button(
            self.window,
            wx.ID_ANY,
            ">",
            wx.DefaultPosition,
            wx.Size(20, -1),
        )
        self.right_btn_ctrl.SetToolTip(__("モーフ組み合わせプルダウンの選択肢を下方向に移動できます。"))
        self.right_btn_ctrl.Bind(wx.EVT_BUTTON, self.on_change_right)
        self.sizer.Add(self.right_btn_ctrl, 0, wx.ALL, 3)

        self.ratio_slider = FloatSliderCtrl(
            parent=self.window,
            value=0,
            min_value=-1,
            max_value=2,
            increment=0.01,
            spin_increment=0.1,
            border=3,
            size=wx.Size(300, -1),
            change_event=self.on_change_morph_ratio,
            tooltip=__("モーフの値を変更できます"),
        )
        self.sizer.Add(self.ratio_slider.sizer, 0, wx.ALL, 3)

    def initialize(self, original_morph_name: str, description: str, morphs: list[Morph]) -> None:
        self.original_name_ctrl.SetValue(original_morph_name)
        self.description_ctrl.SetValue(description)

        # 表示枠に乗ってるモーフのみ対象とする
        self.morph_names = [m.name for m in morphs if 0 <= m.display_slot]
        self.choice_ctrl.AppendItems(self.morph_names)

        if original_morph_name in self.morph_names:
            # 元々のモーフ名と同じモーフがある場合、設定
            self.choice_ctrl.SetSelection([i for i, m in enumerate(self.morph_names) if m == original_morph_name][0])

    def on_change_right(self, event: wx.Event) -> None:
        selection = self.choice_ctrl.GetSelection()
        if selection == len(self.morph_names) - 1:
            selection = -1
        self.choice_ctrl.SetSelection(selection + 1)
        self.on_change_morph(event)

    def on_change_left(self, event: wx.Event) -> None:
        selection = self.choice_ctrl.GetSelection()
        if selection == 0:
            selection = len(self.morph_names)
        self.choice_ctrl.SetSelection(selection - 1)
        self.on_change_morph(event)

    def on_change_morph(self, event: wx.Event) -> None:
        self.ratio_slider.SetValue(0.0)
        self.on_change_morph_ratio(event)

    def on_change_morph_ratio(self, event: wx.Event) -> None:
        morph_name = self.morph_names[self.choice_ctrl.GetSelection()]
        ratio = self.ratio_slider.GetValue()

        motion = VmdMotion()
        motion.morphs[morph_name].append(VmdMorphFrame(0, morph_name, ratio))
        self.parent.canvas.model_sets[0].motion = motion
        self.parent.canvas.change_motion(event, model_index=0)

    def Enable(self, enable: bool) -> None:
        self.choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.ratio_slider.Enable(enable)

    def GetValue(self) -> str:
        # 選択肢が空の場合は元々のモーフ名を代用する
        return self.choice_ctrl.GetStringSelection() or self.original_name_ctrl.GetValue()
