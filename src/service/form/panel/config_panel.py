import os

import wx

from mlib.base.logger import MLogger
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 0.6, 1.0, *args, **kw)

        self._initialize_ui()
        self._initialize_event()

        self.scrolled_window.Layout()
        self.scrolled_window.Fit()
        self.Layout()

        self.on_resize(wx.EVT_SIZE)

    def _initialize_ui(self) -> None:
        self.config_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # 左にビューワー
        self.config_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # --------------
        # 右に設定
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------

        self.scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL,
        )
        self.scrolled_window.SetScrollRate(5, 5)

        self.window_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------
        # 再生

        self.play_sizer = wx.BoxSizer(wx.HORIZONTAL)

        frame_tooltip = __("モーションの任意のキーフレの結果の表示や再生ができます")

        self.frame_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.frame_title_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_title_ctrl, 0, wx.ALL, 3)

        self.frame_ctrl = WheelSpinCtrl(
            self.scrolled_window, initial=0, min=0, max=10000, size=wx.Size(70, -1), change_event=self.on_frame_change
        )
        self.frame_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_ctrl, 0, wx.ALL, 3)

        self.play_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("再生"), wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを指定している場合、再生することができます"))
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.window_sizer.Add(self.play_sizer, 0, wx.ALL, 3)

        # --------------

        # --------------

        self.scrolled_window.SetSizer(self.window_sizer)
        self.right_sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        self.config_sizer.Add(self.right_sizer, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0)
        self.root_sizer.Add(self.config_sizer, 0, wx.ALL, 0)

    def _initialize_event(self) -> None:
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
        else:
            self.start_play()
        self.canvas.on_play(event)

    @property
    def fno(self) -> int:
        return self.frame_ctrl.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        self.frame_ctrl.SetValue(v)

    def stop_play(self) -> None:
        self.play_ctrl.SetLabelText(__("再生"))
        self.Enable(True)

    def start_play(self) -> None:
        self.play_ctrl.SetLabelText(__("停止"))
        self.Enable(False)
        # 停止ボタンだけは有効
        self.play_ctrl.Enable(True)

    def on_resize(self, event: wx.Event):
        self.scrolled_window.SetPosition(wx.Point(self.canvas.size.width, 0))

    def Enable(self, enable: bool):
        self.frame_ctrl.Enable(enable)
        self.play_ctrl.Enable(enable)

    def on_frame_change(self, event: wx.Event):
        self.canvas.change_motion(event, True, 0)
