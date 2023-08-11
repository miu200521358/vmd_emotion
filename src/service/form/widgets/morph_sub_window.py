import os

import wx

from mlib.core.logger import MLogger
from mlib.pmx.canvas import AsyncSubCanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphSubCanvasWindow(BaseFrame):
    def __init__(
        self,
        parent: BaseFrame,
        title: str,
        size: wx.Size,
        look_at_model_names: list[str],
        look_at_bone_names: list[list[str]],
        morph_names: list[str],
        *args,
        **kw,
    ):
        super().__init__(parent.app, title, size, *args, parent=parent, **kw)
        self.panel = MorphSubCanvasPanel(self, look_at_model_names, look_at_bone_names, morph_names)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event: wx.Event):
        # ウィンドウを破棄せずに非表示にする
        self.Hide()
        event.Skip()


class MorphSubCanvasPanel(AsyncSubCanvasPanel):
    def __init__(
        self,
        frame: BaseFrame,
        look_at_model_names: list[str],
        look_at_bone_names: list[list[str]],
        morph_names: list[str],
        *args,
        **kw,
    ):
        super().__init__(frame, look_at_model_names, look_at_bone_names, *args, canvas_height_ratio=0.7, **kw)
        self.morph_names = morph_names

        self.morph_choice_ctrl = wx.Choice(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(300, -1),
            choices=morph_names,
        )
        self.morph_choice_ctrl.SetToolTip(__("置き換えモーフの選択肢\n表示枠に記載されているモーフのみが選択可能です"))
        if len(morph_names):
            self.morph_choice_ctrl.SetSelection(0)
        self.morph_choice_ctrl.Bind(wx.EVT_CHOICE, self.on_change_morph)
        self.root_sizer.Add(self.morph_choice_ctrl, 0, wx.ALL, 3)

        self.morph_ratio_slider = FloatSliderCtrl(
            parent=self,
            value=0,
            min_value=-0.1,
            max_value=1.1,
            increment=0.01,
            spin_increment=0.01,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_morph_ratio,
            tooltip=__("モーフの値を調整した場合の変化をプレビューで確認出来ます"),
        )
        self.root_sizer.Add(self.morph_ratio_slider.sizer, 0, wx.ALL, 3)

    def on_change_morph_ratio(self, event: wx.Event) -> None:
        morph_name = self.morph_names[self.morph_choice_ctrl.GetSelection()]
        ratio = self.morph_ratio_slider.GetValue()

        motion = VmdMotion()
        motion.morphs[morph_name].append(VmdMorphFrame(0, morph_name, ratio))
        self.canvas.model_sets[0].motion = motion
        self.canvas.change_motion(event, model_index=0)

    def on_change_morph(self, event: wx.Event) -> None:
        self.morph_ratio_slider.SetValue(0.0)
        self.on_change_morph_ratio(event)
