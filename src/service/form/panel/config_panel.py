import os

import wx

from mlib.base.logger import MLogger
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl
from mlib.vmd.vmd_collection import VmdMotion
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from service.worker.config.gaze_worker import GazeWorker
from mlib.service.form.widgets.float_slider_ctrl import FloatSliderCtrl

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)
        self.gaze_worker = GazeWorker(self.frame, self.on_config_result)

        self._initialize_ui()
        self._initialize_event()

        self.scrolled_window.Layout()
        self.scrolled_window.Fit()
        self.Layout()

        self.on_resize(wx.EVT_SIZE)

    def _initialize_ui(self) -> None:
        self.canvas_sizer = wx.BoxSizer(wx.VERTICAL)
        # 左にビューワー
        self.canvas_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # --------------
        # 下に設定
        self.config_sizer = wx.BoxSizer(wx.VERTICAL)

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

        self.gaze_infection_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_infection_title_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.gaze_infection_title_ctrl, 0, wx.ALL, 3)

        self.frame_ctrl = WheelSpinCtrl(
            self.scrolled_window, initial=0, min=0, max=10000, size=wx.Size(70, -1), change_event=self.on_frame_change
        )
        self.frame_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_ctrl, 0, wx.ALL, 3)

        self.play_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("再生"), wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを再生することができます（ただし重いです）"))
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.window_sizer.Add(self.play_sizer, 0, wx.ALL, 3)

        # --------------
        # 目線作成

        self.gaze_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_gaze_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("目線生成"), wx.DefaultPosition, wx.Size(120, -1))
        self.create_gaze_ctrl.SetToolTip(__("頭などの動きに合わせて目線を生成します"))
        self.gaze_sizer.Add(self.create_gaze_ctrl, 0, wx.ALL, 3)

        gaze_infection_tooltip = __("目線キーフレを作成する頻度。\n値が小さいほど、小さな動きでも目線が動くようになります。")

        self.gaze_infection_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("目線頻度"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_infection_title_ctrl.SetToolTip(gaze_infection_tooltip)
        self.gaze_sizer.Add(self.gaze_infection_title_ctrl, 0, wx.ALL, 3)

        self.gaze_infection_slider = FloatSliderCtrl(
            parent=self.scrolled_window,
            value=0.05,
            min_value=0.001,
            max_value=0.5,
            increment=0.01,
            spin_increment=0.01,
            border=3,
            size=wx.Size(100, -1),
            tooltip=gaze_infection_tooltip,
        )
        self.gaze_sizer.Add(self.gaze_infection_slider.sizer, 0, wx.ALL, 3)

        gaze_ratio_x_tooltip = __("目線キーフレで設定する縦方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_x_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("目線の縦振り幅"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_ratio_x_title_ctrl.SetToolTip(gaze_ratio_x_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_x_slider = FloatSliderCtrl(
            parent=self.scrolled_window,
            value=0.15,
            min_value=0.1,
            max_value=1.0,
            increment=0.05,
            spin_increment=0.05,
            border=3,
            size=wx.Size(100, -1),
            tooltip=gaze_ratio_x_tooltip,
        )
        self.gaze_sizer.Add(self.gaze_ratio_x_slider.sizer, 0, wx.ALL, 3)

        gaze_ratio_y_tooltip = __("目線キーフレで設定する横方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_y_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("目線の横振り幅"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.gaze_ratio_y_title_ctrl.SetToolTip(gaze_ratio_y_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_y_slider = FloatSliderCtrl(
            parent=self.scrolled_window,
            value=0.2,
            min_value=0.1,
            max_value=1.0,
            increment=0.05,
            spin_increment=0.05,
            border=3,
            size=wx.Size(100, -1),
            tooltip=gaze_ratio_y_tooltip,
        )
        self.gaze_sizer.Add(self.gaze_ratio_y_slider.sizer, 0, wx.ALL, 3)

        self.window_sizer.Add(self.gaze_sizer, 0, wx.ALL, 3)

        # --------------

        self.scrolled_window.SetSizer(self.window_sizer)
        self.config_sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        self.canvas_sizer.Add(self.config_sizer, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0)
        self.root_sizer.Add(self.canvas_sizer, 0, wx.ALL, 0)

        self.console_ctrl = ConsoleCtrl(self.frame, self, rows=1)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

    def _initialize_event(self) -> None:
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)
        self.create_gaze_ctrl.Bind(wx.EVT_BUTTON, self.on_create_gaze)

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
        self.scrolled_window.SetPosition(wx.Point(0, self.canvas.size.height))

    def Enable(self, enable: bool):
        self.frame_ctrl.Enable(enable)
        self.play_ctrl.Enable(enable)
        self.create_gaze_ctrl.Enable(enable)
        self.gaze_infection_slider.Enable(enable)
        self.gaze_ratio_x_slider.Enable(enable)
        self.gaze_ratio_y_slider.Enable(enable)

    def on_frame_change(self, event: wx.Event):
        self.Enable(False)
        self.canvas.change_motion(event, True, 0)
        self.Enable(True)

    def on_create_gaze(self, event: wx.Event) -> None:
        self.Enable(False)
        self.gaze_worker.start()

    def on_config_result(self, result: bool, data: tuple[VmdMotion, VmdMotion], elapsed_time: str):
        # モーションデータを上書きして再読み込み
        motion, output_motion = data
        self.frame.file_panel.motion_ctrl.data = motion
        self.canvas.model_sets[0].motion = motion
        self.frame.file_panel.output_motion_ctrl.data = output_motion

        self.on_frame_change(wx.EVT_BUTTON)

        self.Enable(True)
        self.frame.on_sound()
