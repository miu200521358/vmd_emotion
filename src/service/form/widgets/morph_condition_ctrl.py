import os
from typing import Optional

import wx
from mlib.core.interpolation import Interpolation, evaluate

from mlib.core.logger import MLogger
from mlib.pmx.canvas import PmxCanvas
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.bezier_ctrl import BezierCtrl
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl
from mlib.service.form.widgets.image_btn_ctrl import ImageButton
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl, WheelSpinCtrlDouble
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MorphConditionCtrl:
    def __init__(self, frame: BaseFrame, parent: BasePanel, window: wx.ScrolledWindow, sizer: wx.Sizer, model: PmxModel) -> None:
        self.frame = frame
        self.parent = parent
        self.window = window
        self.sizer = sizer
        self.model = model

        self.bezier_window_size = wx.Size(300, 700)
        self.bezier_window: Optional[BezierWindow] = None

        self.morph_name_ctrl = wx.ComboBox(
            self.window, id=wx.ID_ANY, choices=model.morphs.names, size=wx.Size(200, -1), style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER
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

        self.bezier_view_ctrl: ImageButton = ImageButton(
            self.window,
            "resources/icon/visibility_on.png",
            wx.Size(15, 15),
            self.on_show_bezier,
            __("ボタンをONにすると、補間曲線の形や補間曲線に準拠したモーフの変化をプレビューで確認できます"),
        )
        self.sizer.Add(self.bezier_view_ctrl, 0, wx.ALL, 3)

    def Enable(self, enable: bool) -> None:
        self.morph_name_ctrl.Enable(enable)
        self.start_x_ctrl.Enable(enable)
        self.start_y_ctrl.Enable(enable)
        self.end_x_ctrl.Enable(enable)
        self.end_y_ctrl.Enable(enable)
        self.min_ctrl.Enable(enable)
        self.max_ctrl.Enable(enable)

    def on_show_bezier(self, event: wx.Event) -> None:
        self.parent.Enable(False)
        self.create_bezier_window()

        if self.bezier_window:
            if not self.bezier_window.IsShown():
                self.bezier_window.panel.bezier_ctrl.start_x_ctrl.SetValue(self.start_x_ctrl.GetValue())
                self.bezier_window.panel.bezier_ctrl.start_y_ctrl.SetValue(self.start_y_ctrl.GetValue())
                self.bezier_window.panel.bezier_ctrl.end_x_ctrl.SetValue(self.end_x_ctrl.GetValue())
                self.bezier_window.panel.bezier_ctrl.end_y_ctrl.SetValue(self.end_y_ctrl.GetValue())

                self.bezier_window.panel.canvas.append_model_set(self.model, VmdMotion(), 0.0, True)
                self.bezier_window.panel.canvas.vertical_degrees = 5
                self.bezier_window.panel.canvas.look_at_center = self.model.bones["頭"].position.copy()
                self.bezier_window.panel.canvas.Refresh()

                self.bezier_window.Show()

            elif self.bezier_window.IsShown():
                self.bezier_window.Hide()
        self.parent.Enable(True)
        event.Skip()

    def create_bezier_window(self) -> None:
        if not self.bezier_window:
            self.bezier_window = BezierWindow(self.frame, self, __("補間曲線プレビュー"), self.bezier_window_size)
            frame_x, frame_y = self.frame.GetPosition()
            self.bezier_window.SetPosition(wx.Point(max(0, frame_x + self.frame.GetSize().GetWidth() + 10), max(0, frame_y + 30)))

    def on_enter_choice(self, event: wx.Event) -> None:
        """一致している名前があれば選択"""
        idx = event.GetEventObject().FindString(event.GetEventObject().GetValue())
        if idx >= 0:
            event.GetEventObject().SetSelection(idx)


class BezierWindow(BaseFrame):
    def __init__(self, parent: BaseFrame, condition_ctrl: MorphConditionCtrl, title: str, size: wx.Size, *args, **kw):
        super().__init__(parent.app, title, size, *args, parent=parent, **kw)
        self.condition_ctrl = condition_ctrl
        self.panel = BezierPanel(self, condition_ctrl)

        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event: wx.Event):
        # ウィンドウを破棄せずに非表示にする
        self.Hide()
        event.Skip()

    def on_ok(self, event: wx.Event):
        self.condition_ctrl.start_x_ctrl.SetValue(self.panel.bezier_ctrl.start_x_ctrl.GetValue())
        self.condition_ctrl.start_y_ctrl.SetValue(self.panel.bezier_ctrl.start_y_ctrl.GetValue())
        self.condition_ctrl.end_x_ctrl.SetValue(self.panel.bezier_ctrl.end_x_ctrl.GetValue())
        self.condition_ctrl.end_y_ctrl.SetValue(self.panel.bezier_ctrl.end_y_ctrl.GetValue())

        self.on_close(event)

    def on_cancel(self, event: wx.Event):
        self.on_close(event)


class BezierPanel(BasePanel):
    def __init__(self, frame: BaseFrame, condition_ctrl: MorphConditionCtrl, *args, **kw):
        self.canvas_width_ratio = 1.0
        self.canvas_height_ratio = 0.5
        self.condition_ctrl = condition_ctrl
        self.is_view_bezier = True

        super().__init__(frame)

        self.bezier_ctrl = BezierCtrl(frame, self, wx.Size(160, 160))
        self.root_sizer.Add(self.bezier_ctrl.sizer, 0, wx.ALL, 5)

        self.canvas = PmxCanvas(self, True)
        self.root_sizer.Add(self.canvas, 0, wx.ALL, 5)

        self.slider = FloatSliderCtrl(
            parent=self,
            value=0,
            min_value=0,
            max_value=1,
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

        self.ok_ctrl = wx.Button(self, wx.ID_ANY, __("条件追加"), wx.DefaultPosition, wx.Size(120, -1))
        self.ok_ctrl.SetToolTip(__("調整条件を追加できます"))
        self.ok_ctrl.Bind(wx.EVT_BUTTON, self.frame.on_ok)
        self.btn_sizer.Add(self.ok_ctrl, 0, wx.ALL, 3)

        self.cancel_ctrl = wx.Button(self, wx.ID_ANY, __("条件全削除"), wx.DefaultPosition, wx.Size(120, -1))
        self.cancel_ctrl.SetToolTip(__("全ての調整条件を削除できます"))
        self.cancel_ctrl.Bind(wx.EVT_BUTTON, self.frame.on_cancel)
        self.btn_sizer.Add(self.cancel_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.btn_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 3)

    def on_change_ratio(self, event: wx.Event) -> None:
        interpolation = Interpolation()
        interpolation.start.x = self.bezier_ctrl.start_x_ctrl.GetValue()
        interpolation.start.y = self.bezier_ctrl.start_y_ctrl.GetValue()
        interpolation.end.x = self.bezier_ctrl.end_x_ctrl.GetValue()
        interpolation.end.y = self.bezier_ctrl.end_y_ctrl.GetValue()

        _, ry, _ = evaluate(interpolation, 0, int(self.slider.GetValue() * 100), 100)
        ratio = self.slider.GetValue() * ry if self.is_view_bezier else self.slider.GetValue()

        motion = VmdMotion()
        motion.append_morph_frame(VmdMorphFrame(0, self.condition_ctrl.morph_name_ctrl.GetStringSelection(), ratio))
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
