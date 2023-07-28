import os

import wx

from mlib.base.logger import MLogger
from mlib.pmx.canvas import CanvasPanel
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.frame_slider_ctrl import FrameSliderCtrl
from mlib.service.form.widgets.spin_ctrl import WheelSpinCtrl, WheelSpinCtrlDouble
from mlib.vmd.vmd_collection import VmdMotion
from service.form.widgets.blink_ctrl_set import BlinkCtrlSet
from service.worker.config.blink_worker import BlinkWorker
from service.worker.config.gaze_worker import GazeWorker
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.form.widgets.morph_ctrl_set import MorphCtrlSet

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ConfigPanel(CanvasPanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)
        self.gaze_worker = GazeWorker(self.frame, self.on_config_result)
        self.blink_worker = BlinkWorker(self.frame, self.on_config_result)
        self.bone_matrixes = VmdBoneFrameTrees()
        self.show_config = True

        # -------------------

        self.canvas_sizer = wx.BoxSizer(wx.VERTICAL)
        # 上にビューワー
        self.canvas_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        # 下に設定
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # -------------------

        self._initialize_ui_config()
        self._initialize_ui_morph()

        # -------------------

        self.change_window()

        self.canvas_sizer.Add(self.sizer, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 0)
        self.root_sizer.Add(self.canvas_sizer, 0, wx.ALL, 0)

        self.console_ctrl = ConsoleCtrl(self.frame, self, rows=1)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

        # -------------------

        self.fit_window()

        self.on_resize(wx.EVT_SIZE)

    def _initialize_ui_morph(self) -> None:
        # --------------
        self.morph_scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL,
        )
        self.morph_scrolled_window.SetScrollRate(5, 5)

        self.morph_window_sizer = wx.BoxSizer(wx.VERTICAL)

        self.morph_set = MorphCtrlSet(self, self.morph_scrolled_window)
        self.morph_window_sizer.Add(self.morph_set.sizer, 0, wx.ALL, 3)

        self.morph_scrolled_window.SetSizer(self.morph_window_sizer)
        self.sizer.Add(self.morph_scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

    def _initialize_ui_config(self) -> None:
        self.config_scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL,
        )
        self.config_scrolled_window.SetScrollRate(5, 5)

        self.config_window_sizer = wx.BoxSizer(wx.VERTICAL)

        # --------------
        # 再生

        self.play_sizer = wx.BoxSizer(wx.HORIZONTAL)

        frame_tooltip = __("モーションの任意のキーフレの結果の表示や再生ができます")

        self.gaze_infection_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_infection_title_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.gaze_infection_title_ctrl, 0, wx.ALL, 3)

        # スライダー
        self.frame_slider = FrameSliderCtrl(
            self.config_scrolled_window, border=3, size=wx.Size(900, -1), tooltip=frame_tooltip, change_event=self.on_frame_change
        )
        self.play_sizer.Add(self.frame_slider.sizer, 0, wx.ALL, 0)

        # self.frame_ctrl = WheelSpinCtrl(
        #     self.scrolled_window, initial=0, min=0, max=10000, size=wx.Size(70, -1), change_event=self.on_frame_change
        # )
        # self.frame_ctrl.SetToolTip(frame_tooltip)
        # self.play_sizer.Add(self.frame_ctrl, 0, wx.ALL, 3)

        self.play_ctrl = wx.Button(self.config_scrolled_window, wx.ID_ANY, __("再生"), wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを再生することができます（ただし重いです）"))
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.config_window_sizer.Add(self.play_sizer, 0, wx.ALL, 3)

        # --------------
        # 目線作成

        self.gaze_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_gaze_ctrl = wx.Button(self.config_scrolled_window, wx.ID_ANY, __("目線生成"), wx.DefaultPosition, wx.Size(120, -1))
        self.create_gaze_ctrl.SetToolTip(__("頭などの動きに合わせて目線を生成します"))
        self.create_gaze_ctrl.Bind(wx.EVT_BUTTON, self.on_create_gaze)
        self.gaze_sizer.Add(self.create_gaze_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_infection_tooltip = __("目線キーフレを作成する頻度。\n値が大きいほど、小さな動きでも目線が動くようになります。")

        self.gaze_infection_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("頻度"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_infection_title_ctrl.SetToolTip(gaze_infection_tooltip)
        self.gaze_sizer.Add(self.gaze_infection_title_ctrl, 0, wx.ALL, 3)

        self.gaze_infection_ctrl = WheelSpinCtrlDouble(
            self.config_scrolled_window, initial=0.5, min=0.1, max=1.0, inc=0.01, size=wx.Size(60, -1)
        )
        self.gaze_infection_ctrl.SetToolTip(gaze_infection_tooltip)
        self.gaze_sizer.Add(self.gaze_infection_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_ratio_x_tooltip = __("目線キーフレで設定する縦方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_x_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("縦振り幅"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_ratio_x_title_ctrl.SetToolTip(gaze_ratio_x_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_x_ctrl = WheelSpinCtrlDouble(
            self.config_scrolled_window, initial=0.7, min=0.5, max=1.5, inc=0.01, size=wx.Size(60, -1)
        )
        self.gaze_ratio_x_ctrl.SetToolTip(gaze_ratio_x_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_upper_x_tooltip = __("目線キーフレで設定する縦方向の値の上限。\n上限を超えた回転量になった場合、上限までしか動かしません。")

        self.gaze_limit_upper_x_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("縦上限"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_limit_upper_x_title_ctrl.SetToolTip(gaze_limit_upper_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_upper_x_ctrl = WheelSpinCtrl(self.config_scrolled_window, initial=3, min=0, max=45, size=wx.Size(60, -1))
        self.gaze_limit_upper_x_ctrl.SetToolTip(gaze_limit_upper_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_lower_x_tooltip = __("目線キーフレで設定する縦方向の値の下限。\n下限を超えた回転量になった場合、下限までしか動かしません。")

        self.gaze_limit_lower_x_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("縦下限"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_limit_lower_x_title_ctrl.SetToolTip(gaze_limit_lower_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_x_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_lower_x_ctrl = WheelSpinCtrl(self.config_scrolled_window, initial=-8, min=-45, max=0, size=wx.Size(60, -1))
        self.gaze_limit_lower_x_ctrl.SetToolTip(gaze_limit_lower_x_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_x_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_ratio_y_tooltip = __("目線キーフレで設定する横方向の値の大きさ。\n値が大きいほど、目線を大きく動かすようになります。")

        self.gaze_ratio_y_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("横振り幅"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_ratio_y_title_ctrl.SetToolTip(gaze_ratio_y_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_ratio_y_ctrl = WheelSpinCtrlDouble(
            self.config_scrolled_window, initial=0.7, min=0.5, max=1.5, inc=0.01, size=wx.Size(60, -1)
        )
        self.gaze_ratio_y_ctrl.SetToolTip(gaze_ratio_y_tooltip)
        self.gaze_sizer.Add(self.gaze_ratio_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_upper_y_tooltip = __("目線キーフレで設定する横方向の値の上限（向かって左側）。\n上限を超えた回転量になった場合、上限までしか動かしません。")

        self.gaze_limit_upper_y_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("横上限"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_limit_upper_y_title_ctrl.SetToolTip(gaze_limit_upper_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_upper_y_ctrl = WheelSpinCtrl(self.config_scrolled_window, initial=13, min=0, max=45, size=wx.Size(60, -1))
        self.gaze_limit_upper_y_ctrl.SetToolTip(gaze_limit_upper_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_upper_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_limit_lower_y_tooltip = __("目線キーフレで設定する横方向の値の下限（向かって右側）。\n下限を超えた回転量になった場合、下限までしか動かしません。")

        self.gaze_limit_lower_y_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("横下限"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_limit_lower_y_title_ctrl.SetToolTip(gaze_limit_lower_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_y_title_ctrl, 0, wx.ALL, 3)

        self.gaze_limit_lower_y_ctrl = WheelSpinCtrl(self.config_scrolled_window, initial=-13, min=-45, max=0, size=wx.Size(60, -1))
        self.gaze_limit_lower_y_ctrl.SetToolTip(gaze_limit_lower_y_tooltip)
        self.gaze_sizer.Add(self.gaze_limit_lower_y_ctrl, 0, wx.ALL, 3)

        # --------------
        gaze_reset_tooltip = __("目線をリセットするキーフレ間隔\n値が小さいほど、目線を細かくリセットします")

        self.gaze_reset_title_ctrl = wx.StaticText(
            self.config_scrolled_window, wx.ID_ANY, __("リセット"), wx.DefaultPosition, wx.DefaultSize, 0
        )
        self.gaze_reset_title_ctrl.SetToolTip(gaze_reset_tooltip)
        self.gaze_sizer.Add(self.gaze_reset_title_ctrl, 0, wx.ALL, 3)

        self.gaze_reset_ctrl = WheelSpinCtrl(self.config_scrolled_window, initial=7, min=5, max=15, size=wx.Size(60, -1))
        self.gaze_reset_ctrl.SetToolTip(gaze_reset_tooltip)
        self.gaze_sizer.Add(self.gaze_reset_ctrl, 0, wx.ALL, 3)

        # --------------
        self.config_window_sizer.Add(self.gaze_sizer, 0, wx.ALL, 3)

        # --------------
        # まばたき作成

        self.blink_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.create_blink_ctrl = wx.Button(self.config_scrolled_window, wx.ID_ANY, __("まばたき生成"), wx.DefaultPosition, wx.Size(120, -1))
        self.create_blink_ctrl.SetToolTip(__("頭などの動きに合わせてをまばたきを生成します。"))
        self.create_blink_ctrl.Bind(wx.EVT_BUTTON, self.on_create_blink)
        self.blink_sizer.Add(self.create_blink_ctrl, 0, wx.ALL, 3)

        self.blink_set = BlinkCtrlSet(self, self.config_scrolled_window)
        self.blink_sizer.Add(self.blink_set.sizer, 0, wx.ALL, 3)

        self.config_window_sizer.Add(self.blink_sizer, 0, wx.ALL, 3)
        self.config_scrolled_window.SetSizer(self.config_window_sizer)
        self.sizer.Add(self.config_scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

    def change_window(self):
        if self.show_config:
            self.morph_scrolled_window.Hide()
            self.config_scrolled_window.Show()
        else:
            self.config_scrolled_window.Hide()
            self.morph_scrolled_window.Show()
        self.sizer.Layout()

    def fit_window(self):
        if self.show_config:
            self.config_scrolled_window.Layout()
            self.config_scrolled_window.Fit()
        else:
            self.morph_scrolled_window.Layout()
            self.morph_scrolled_window.Fit()
        self.Layout()

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
        else:
            self.start_play()
        self.canvas.on_play(event)

    @property
    def fno(self) -> int:
        return self.frame_slider.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        self.frame_slider.SetValue(v)

    def stop_play(self) -> None:
        self.play_ctrl.SetLabelText(__("再生"))
        self.Enable(True)

    def start_play(self) -> None:
        self.play_ctrl.SetLabelText(__("停止"))
        self.Enable(False)
        # 停止ボタンだけは有効
        self.play_ctrl.Enable(True)

    def on_resize(self, event: wx.Event):
        self.config_scrolled_window.SetPosition(wx.Point(0, self.canvas.size.height))

    def Enable(self, enable: bool):
        self.frame_slider.Enable(enable)
        self.play_ctrl.Enable(enable)
        self.create_gaze_ctrl.Enable(enable)
        self.gaze_infection_ctrl.Enable(enable)
        self.gaze_ratio_x_ctrl.Enable(enable)
        self.gaze_limit_upper_x_ctrl.Enable(enable)
        self.gaze_limit_lower_x_ctrl.Enable(enable)
        self.gaze_ratio_y_ctrl.Enable(enable)
        self.gaze_limit_upper_y_ctrl.Enable(enable)
        self.gaze_limit_lower_y_ctrl.Enable(enable)
        self.gaze_reset_ctrl.Enable(enable)

        self.create_blink_ctrl.Enable(enable)
        self.blink_set.Enable(enable)

    def on_frame_change(self, event: wx.Event):
        self.Enable(False)
        self.canvas.change_motion(event, True, 0)
        self.Enable(True)

    def on_create_gaze(self, event: wx.Event) -> None:
        self.Enable(False)
        self.gaze_worker.start()

    def on_create_blink(self, event: wx.Event) -> None:
        self.Enable(False)
        self.blink_worker.start()

    def on_config_result(self, result: bool, data: tuple[VmdMotion, VmdMotion], elapsed_time: str):
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        # モーションデータを上書きして再読み込み
        motion, output_motion = data
        self.frame.file_panel.motion_ctrl.data = motion
        self.canvas.model_sets[0].motion = motion
        self.frame.file_panel.output_motion_ctrl.data = output_motion
        # 関連ボーン・モーフのキーがある箇所に飛ぶ
        key_fnos = [fno for bone_name in ("両目", "左目", "右目") for fno in output_motion.bones[bone_name].indexes] + [
            fno for bone_name in ("まばたき", "あ", "い", "う", "え", "お") for fno in output_motion.bones[bone_name].indexes
        ]
        self.frame_slider.SetKeyFrames(sorted(set(key_fnos)))

        self.on_frame_change(wx.EVT_BUTTON)

        self.Enable(True)
        self.frame.on_sound()

    def show_bone_weight(self, is_show_bone_weight: bool) -> None:
        self.frame.show_bone_weight(is_show_bone_weight)
