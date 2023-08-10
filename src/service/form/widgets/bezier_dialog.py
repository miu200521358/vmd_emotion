import os

import wx
from mlib.core.interpolation import Interpolation, evaluate

from mlib.core.logger import MLogger
from mlib.pmx.canvas import PmxCanvas
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.bezier_ctrl import BezierCtrl
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.service.form.widgets.image_btn_ctrl import ImageButton
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame
from service.form.widgets.morph_condition_ctrl import MorphConditionCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class BezierDialog(wx.Dialog):
    def __init__(self, parent: BaseFrame, panel: BasePanel, title: str, size: wx.Size, *args, **kw):
        super().__init__(parent, *args, title=title, size=size, **kw)
        self.panel = panel
        self.bezier_panel = BezierPanel(self)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event: wx.Event):
        # ウィンドウを破棄せずに非表示にする
        self.Hide()
        event.Skip()

    def on_ok(self, event: wx.Event):
        condition_ctrl: MorphConditionCtrl = self.panel.conditions[self.panel.bezier_target_idx]

        condition_ctrl.start_x_ctrl.SetValue(self.bezier_panel.bezier_ctrl.start_x_ctrl.GetValue())
        condition_ctrl.start_y_ctrl.SetValue(self.bezier_panel.bezier_ctrl.start_y_ctrl.GetValue())
        condition_ctrl.end_x_ctrl.SetValue(self.bezier_panel.bezier_ctrl.end_x_ctrl.GetValue())
        condition_ctrl.end_y_ctrl.SetValue(self.bezier_panel.bezier_ctrl.end_y_ctrl.GetValue())

        self.on_close(event)

    def on_cancel(self, event: wx.Event):
        self.on_close(event)


class BezierPanel(BasePanel):
    def __init__(self, frame: BaseFrame, *args, **kw):
        self.canvas_width_ratio = 1.0
        self.canvas_height_ratio = 0.5
        self.is_view_bezier = True

        super().__init__(frame)

        self.bezier_ctrl = BezierCtrl(frame, self, wx.Size(160, 160), change_event=self.on_change_ratio)
        self.root_sizer.Add(self.bezier_ctrl.sizer, 0, wx.ALL, 5)

        self.canvas = PmxCanvas(self, True)
        self.root_sizer.Add(self.canvas, 0, wx.ALL, 5)

        condition_ctrl: MorphConditionCtrl = self.frame.panel.conditions[self.frame.panel.bezier_target_idx]

        self.slider = FloatSliderCtrl(
            parent=self,
            value=0,
            min_value=condition_ctrl.min_ctrl.GetValue(),
            max_value=condition_ctrl.max_ctrl.GetValue(),
            increment=0.01,
            spin_increment=0.01,
            border=3,
            size=wx.Size(200, -1),
            change_event=self.on_change_ratio,
            tooltip=__("モーフの値を調整した場合の変化をプレビューで確認出来ます"),
        )
        self.root_sizer.Add(self.slider.sizer, 0, wx.ALL, 5)

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.view_off_ctrl: ImageButton = ImageButton(
            self,
            "resources/icon/visibility_on.png",
            wx.Size(15, 15),
            self.on_view_bezier,
            __("ボタンをOFFにすると元々のモーフの変化量による変化に切り替えられます\nもう一度ONにすると、補間曲線に準拠した変化量になります"),
        )
        self.view_off_ctrl.SetBackgroundColour(self.active_background_color)
        self.btn_sizer.Add(self.view_off_ctrl, 0, wx.ALL, 3)

        self.ok_ctrl = wx.Button(self, wx.ID_ANY, "OK", wx.DefaultPosition, wx.Size(60, -1))
        self.ok_ctrl.SetToolTip(__("補間曲線をメイン画面に適用します"))
        self.ok_ctrl.Bind(wx.EVT_BUTTON, self.frame.on_ok)
        self.btn_sizer.Add(self.ok_ctrl, 0, wx.ALL, 3)

        self.cancel_ctrl = wx.Button(self, wx.ID_ANY, "Cancel", wx.DefaultPosition, wx.Size(60, -1))
        self.cancel_ctrl.SetToolTip(__("補間曲線を適用せずにウィンドウを閉じます"))
        self.cancel_ctrl.Bind(wx.EVT_BUTTON, self.frame.on_cancel)
        self.btn_sizer.Add(self.cancel_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 3)

    def on_change_ratio(self, event: wx.Event) -> None:
        condition_ctrl: MorphConditionCtrl = self.frame.panel.conditions[self.frame.panel.bezier_target_idx]

        interpolation = Interpolation()
        interpolation.start.x = self.bezier_ctrl.start_x_ctrl.GetValue()
        interpolation.start.y = self.bezier_ctrl.start_y_ctrl.GetValue()
        interpolation.end.x = self.bezier_ctrl.end_x_ctrl.GetValue()
        interpolation.end.y = self.bezier_ctrl.end_y_ctrl.GetValue()

        min_v = 0
        max_v = int(condition_ctrl.max_ctrl.GetValue() * 100) + int(abs(condition_ctrl.min_ctrl.GetValue()) * 100)

        _, ry, _ = evaluate(interpolation, min_v, int((self.slider.GetValue() + abs(condition_ctrl.min_ctrl.GetValue())) * 100), max_v)
        ratio = self.slider.GetValue() * ry if self.is_view_bezier else self.slider.GetValue()

        motion = VmdMotion()
        motion.append_morph_frame(VmdMorphFrame(0, condition_ctrl.morph_name_ctrl.GetStringSelection(), ratio))
        self.canvas.model_sets[0].motion = motion
        self.canvas.change_motion(event, is_bone_deform=False)

    def on_view_bezier(self, event: wx.Event):
        if not self.is_view_bezier:
            self.view_off_ctrl.SetBackgroundColour(self.active_background_color)
            self.view_off_ctrl.SetBitmap(self.view_off_ctrl.create_bitmap("resources/icon/visibility_on.png"))
        else:
            self.view_off_ctrl.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            self.view_off_ctrl.SetBitmap(self.view_off_ctrl.create_bitmap("resources/icon/visibility_off.png"))
        self.is_view_bezier = not self.is_view_bezier
        self.on_change_ratio(event)

    def get_canvas_size(self) -> wx.Size:
        w, h = self.frame.GetClientSize()
        canvas_width = w * self.canvas_width_ratio
        if canvas_width % 2 != 0:
            # 2で割り切れる値にする
            canvas_width += 1
        canvas_height = h * self.canvas_height_ratio
        return wx.Size(int(canvas_width), int(canvas_height))

    def on_resize(self, event: wx.Event):
        pass

    @property
    def fno(self) -> int:
        return 0

    @fno.setter
    def fno(self, v: int) -> None:
        pass
