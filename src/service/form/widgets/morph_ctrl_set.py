import os
from typing import Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.canvas import PreviewCanvasWindow
from mlib.pmx.pmx_collection import Morphs, PmxModel
from mlib.pmx.pmx_part import Morph, MorphPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrlDouble
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphCtrlSet:
    def __init__(self, frame: BaseFrame, parent: BasePanel, window: wx.ScrolledWindow) -> None:
        self.frame = frame
        self.parent = parent
        self.window = window

        self.morphs: Morphs = Morphs()

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.morph_title_ctrl = wx.StaticText(self.window, wx.ID_ANY, __("モーフ置換設定"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.morph_title_ctrl.SetToolTip(__("ツールで生成するモーフ名をモデルに合わせて変更できます"))
        self.sizer.Add(self.morph_title_ctrl, 0, wx.ALL, 3)

        self.below_eyebrow_morph_ctrl = MorphReplaceSet(self.parent, self.window, self)
        self.sizer.Add(self.below_eyebrow_morph_ctrl.sizer, 0, wx.ALL, 3)

        self.blink_morph_ctrl = MorphReplaceSet(self.parent, self.window, self)
        self.sizer.Add(self.blink_morph_ctrl.sizer, 0, wx.ALL, 3)

        self.smile_morph_ctrl = MorphReplaceSet(self.parent, self.window, self)
        self.sizer.Add(self.smile_morph_ctrl.sizer, 0, wx.ALL, 3)

        # 顔アップ
        self.preview_window_btn = wx.Button(self.window, wx.ID_ANY, __("プレビュー"), wx.DefaultPosition, wx.Size(80, -1))
        self.preview_window_btn.SetToolTip(__("選択されたモーフによる変化をサブウィンドウで確認できます"))
        self.preview_window_btn.Bind(wx.EVT_BUTTON, self.on_show_preview_window)
        self.sizer.Add(self.preview_window_btn, 0, wx.ALL, 3)

        self.preview_window_size = wx.Size(300, 300)
        self.preview_window: Optional[PreviewCanvasWindow] = None

    def on_show_preview_window(self, event: wx.Event) -> None:
        self.create_preview_window()

        if self.preview_window:
            if not self.preview_window.IsShown():
                self.preview_window.Show()
            elif self.preview_window.IsShown():
                self.preview_window.Hide()
        event.Skip()

    def create_preview_window(self) -> None:
        model: Optional[PmxModel] = self.parent.model_ctrl.data
        if not self.preview_window and model:
            self.preview_window = PreviewCanvasWindow(
                self.frame, __("モーフプレビュー"), self.preview_window_size, [model.name], [model.bones.names]
            )
            self.preview_window.panel.canvas.clear_model_set()
            self.preview_window.panel.canvas.append_model_set(model, VmdMotion(), 0.0, True)
            frame_x, frame_y = self.frame.GetPosition()
            self.preview_window.SetPosition(wx.Point(max(0, frame_x - self.preview_window_size.x - 10), max(0, frame_y)))

    def initialize(self, morphs: Morphs) -> None:
        self.morphs = morphs
        self.below_eyebrow_morph_ctrl.initialize("下", morphs.filter_by_panel(MorphPanel.EYEBROW_LOWER_LEFT) if morphs else [])
        self.blink_morph_ctrl.initialize("まばたき", morphs.filter_by_panel(MorphPanel.EYE_UPPER_LEFT) if morphs else [])
        self.smile_morph_ctrl.initialize("笑い", morphs.filter_by_panel(MorphPanel.EYE_UPPER_LEFT) if morphs else [])

    def Enable(self, enable: bool) -> None:
        self.below_eyebrow_morph_ctrl.Enable(enable)
        self.blink_morph_ctrl.Enable(enable)
        self.smile_morph_ctrl.Enable(enable)
        self.preview_window_btn.Enable(enable)


class MorphReplaceSet:
    def __init__(self, parent: BasePanel, window: wx.Window, morph_set: "MorphCtrlSet") -> None:
        self.parent = parent
        self.window = window
        self.morph_set = morph_set
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.morph_names: list[str] = []

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
            wx.Size(100, -1),
            choices=[],
        )
        self.choice_ctrl.SetToolTip(__("置き換えモーフの選択肢\n表示枠に記載されているモーフのみが選択可能です"))
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

        self.ratio_ctrl = WheelSpinCtrlDouble(
            self.window, initial=0.0, min=-2.0, max=2.0, inc=0.01, size=wx.Size(60, -1), change_event=self.on_change_morph_ratio
        )
        self.ratio_ctrl.SetToolTip(__("モーフの値を変更して、プレビューで動作を確認出来ます。"))
        self.sizer.Add(self.ratio_ctrl, 0, wx.ALL, 3)

    def initialize(self, original_morph_name: str, morphs: list[Morph]) -> None:
        self.original_name_ctrl.SetValue(original_morph_name)

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
        self.ratio_ctrl.SetValue(0.0)
        self.on_change_morph_ratio(event)

    def on_change_morph_ratio(self, event: wx.Event) -> None:
        morph_name = self.morph_names[self.choice_ctrl.GetSelection()]
        ratio = self.ratio_ctrl.GetValue()

        motion = VmdMotion()
        motion.morphs[morph_name].append(VmdMorphFrame(0, morph_name, ratio))
        if self.morph_set.preview_window and self.morph_set.preview_window.Shown:
            self.morph_set.preview_window.panel.canvas.model_sets[0].motion = motion
            self.morph_set.preview_window.panel.canvas.change_motion(event, model_index=0)

    def Enable(self, enable: bool) -> None:
        self.choice_ctrl.Enable(enable)
        self.left_btn_ctrl.Enable(enable)
        self.right_btn_ctrl.Enable(enable)
        self.ratio_ctrl.Enable(enable)

    def GetValue(self) -> str:
        # 選択肢が空の場合は元々のモーフ名を代用する
        return self.choice_ctrl.GetStringSelection() or self.original_name_ctrl.GetValue()
