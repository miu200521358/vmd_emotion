import os
from datetime import datetime
from typing import Any, Iterable, Optional

import wx

from mlib.core.logger import ConsoleHandler, MLogger
from mlib.pmx.canvas import CanvasPanel, SubCanvasWindow
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.exec_btn_ctrl import ExecButton
from mlib.service.form.widgets.file_ctrl import MPmxFilePickerCtrl, MVmdFilePickerCtrl
from mlib.service.form.widgets.frame_slider_ctrl import FrameSliderCtrl
from mlib.utils.file_utils import save_histories, separate_path
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.worker.load_worker import LoadWorker
from service.worker.save_worker import SaveWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ServiceCanvasPanel(CanvasPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, 1.0, 0.4, *args, **kw)
        self.enabled_save = False

        self.sub_window_size = wx.Size(300, 300)
        self.sub_window: Optional[SubCanvasWindow] = None

        self.load_worker = LoadWorker(frame, self, self.on_preparer_result)
        self.load_worker.panel = self

        self.service_worker = self.create_service_worker()

        self.save_worker = SaveWorker(frame, self, self.on_save_result)
        self.save_worker.panel = self

        # 上にビューワー
        self.root_sizer.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 0)

        self._initialize_ui()

        self.fit_window()

        self.on_resize(wx.EVT_SIZE)

        # 初期状態は一旦非活性
        self.Enable(False)

        # 初期状態でファイル系と読み込みボタンは有効
        self.EnableLoad(True)

    @property
    def emotion_type(self) -> str:
        return "表情"

    @property
    def exec_label(self) -> str:
        return f"{self.emotion_type}生成"

    @property
    def console_rows(self) -> int:
        return 100

    @property
    def key_names(self) -> Iterable[str]:
        return []

    def create_service_worker(self) -> BaseWorker:
        return BaseWorker(self.frame, self.on_exec_result)

    def _initialize_ui(self) -> None:
        self.scrolled_window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL,
        )
        self.scrolled_window.SetScrollRate(5, 5)

        self.window_sizer = wx.BoxSizer(wx.VERTICAL)

        # ファイル -------------------------

        self.model_ctrl = MPmxFilePickerCtrl(
            self.scrolled_window,
            self.frame,
            self,
            key="model_pmx",
            title="人物モデル",
            is_show_name=True,
            name_spacer=3,
            is_save=False,
            tooltip=f"{self.emotion_type}を付けたい人物モデルを指定してください",
            file_change_event=self.on_change_model_pmx,
        )
        self.model_ctrl.set_parent_sizer(self.window_sizer)

        self.motion_ctrl = MVmdFilePickerCtrl(
            self.scrolled_window,
            self.frame,
            self,
            key="motion_vmd",
            title="表示モーション",
            is_show_name=True,
            name_spacer=1,
            is_save=False,
            tooltip=f"{self.emotion_type}を付けたいモーションを指定してください",
            file_change_event=self.on_change_motion,
        )
        self.motion_ctrl.set_parent_sizer(self.window_sizer)

        self.output_motion_ctrl = MVmdFilePickerCtrl(
            self.scrolled_window,
            self.frame,
            self,
            title=f"{self.emotion_type}モーション出力先",
            is_show_name=False,
            is_save=True,
            tooltip=f"{self.emotion_type}モーションの出力ファイルパスです\n任意の値に変更可能です",
        )
        self.output_motion_ctrl.set_parent_sizer(self.window_sizer)

        # プレビュー ---------------------------
        self.play_sizer = wx.BoxSizer(wx.HORIZONTAL)

        frame_tooltip = "\n".join(
            [
                __("モーションの任意のキーフレの結果の表示や再生ができます"),
                __(f"{self.emotion_type}を生成した後、スライダー上でホイールを動かすと生成キーフレにジャンプできます"),
            ]
        )

        self.frame_title_ctrl = wx.StaticText(self.scrolled_window, wx.ID_ANY, __("モーション"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.frame_title_ctrl.SetToolTip(frame_tooltip)
        self.play_sizer.Add(self.frame_title_ctrl, 0, wx.ALL, 3)

        # スライダー
        self.frame_slider = FrameSliderCtrl(
            self.scrolled_window, border=3, size=wx.Size(860, -1), tooltip=frame_tooltip, change_event=self.on_frame_change
        )
        self.play_sizer.Add(self.frame_slider.sizer, 0, wx.ALL, 0)

        self.play_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("再生"), wx.DefaultPosition, wx.Size(80, -1))
        self.play_ctrl.SetToolTip(__("モーションを再生することができます（ただし重いです）"))
        self.play_ctrl.Bind(wx.EVT_BUTTON, self.on_play)
        self.play_sizer.Add(self.play_ctrl, 0, wx.ALL, 3)

        self.sub_window_ctrl = wx.Button(self.scrolled_window, wx.ID_ANY, __("顔アップ"), wx.DefaultPosition, wx.Size(80, -1))
        self.sub_window_ctrl.SetToolTip(__("顔アップ固定のプレビューをサブウィンドウで確認出来ます"))
        self.sub_window_ctrl.Bind(wx.EVT_BUTTON, self.on_show_sub_window)
        self.play_sizer.Add(self.sub_window_ctrl, 0, wx.ALL, 3)

        self.window_sizer.Add(self.play_sizer, 0, wx.ALL, 3)

        # 個別サービス ---------------------------

        # 個別サービス用UIを追加
        self._initialize_service_ui()

        self.scrolled_window.SetSizer(self.window_sizer)
        self.root_sizer.Add(self.scrolled_window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        # ボタン -------------------------

        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.prepare_btn_ctrl = ExecButton(
            self.scrolled_window,
            self,
            __("データ読み込み"),
            __("データ読み込み停止"),
            self.prepare,
            250,
            __("指定されたモデルとモーションを読み込みます。"),
        )
        self.btn_sizer.Add(self.prepare_btn_ctrl, 0, wx.ALL, 3)

        self.exec_btn_ctrl = ExecButton(
            self.scrolled_window,
            self,
            __(f"{self.exec_label}"),
            __(f"{self.exec_label}停止"),
            self.exec,
            250,
            __(f"生成した{self.emotion_type}をVMDモーションデータとして出力します\nデータ読み込み後、クリックできるようになります"),
        )
        self.btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 3)

        self.save_btn_ctrl = ExecButton(
            self.scrolled_window,
            self,
            __(f"{self.emotion_type}モーション出力"),
            __(f"{self.emotion_type}モーション出力停止"),
            self.save,
            250,
            __(f"生成した{self.emotion_type}をVMDモーションデータとして出力します\n{self.emotion_type}生成実行後、クリックできるようになります"),
        )
        self.btn_sizer.Add(self.save_btn_ctrl, 0, wx.ALL, 3)

        self.window_sizer.Add(self.btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        # コンソール -----------------
        self.console_ctrl = ConsoleCtrl(self, self.frame, self, rows=self.console_rows)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

    def _initialize_service_ui(self) -> None:
        pass

    def prepare(self, event: wx.Event) -> None:
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)

        if not self.load_worker.started:
            if not self.model_ctrl.valid():
                self.Enable(False)
                self.EnableLoad(True)

                logger.warning("人物モデル欄に有効なパスが設定されていない為、読み込みを中断します。")
                return
            if not self.motion_ctrl.valid():
                self.Enable(False)
                self.EnableLoad(True)

                logger.warning("モーション欄に有効なパスが設定されていない為、読み込みを中断します。")
                return

            if not self.model_ctrl.data or not self.motion_ctrl.data:
                # 読み込む
                self.canvas.clear_model_set()
                self.save_histories()

                self.frame.running_worker = True
                self.Enable(False)
                self.load_worker.start()
            else:
                # 既に読み取りが完了していたらそのまま表示
                self.canvas.model_sets[0].motion = self.motion_ctrl.data
                self.canvas.look_at_center = self.canvas.shader.INITIAL_LOOK_AT_CENTER_POSITION.copy()
                self.canvas.vertical_degrees = self.canvas.shader.INITIAL_VERTICAL_DEGREES
                self.canvas.change_motion(event, model_index=0)
                self.canvas.Refresh()

    def save_histories(self) -> None:
        self.model_ctrl.save_path()
        self.motion_ctrl.save_path()

        save_histories(self.frame.histories)

    def on_preparer_result(
        self,
        result: bool,
        data: Optional[tuple[PmxModel, PmxModel, VmdMotion, VmdMotion, dict[str, float], VmdBoneFrameTrees]],
        elapsed_time: str,
    ):
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.frame.running_worker = False
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.Enable(False)
            self.EnableLoad(True)
            self.frame.on_sound()
            return

        logger.info("描画準備開始", decoration=MLogger.Decoration.BOX)

        original_model, model, original_motion, motion, blink_conditions, bone_matrixes = data

        logger.debug("結果展開")

        self.model_ctrl.original_data = original_model
        self.model_ctrl.data = model
        self.frame.models[original_model.digest] = original_model

        logger.debug("モデルデータ設定")

        self.motion_ctrl.original_data = original_motion
        self.motion_ctrl.data = motion
        self.frame.motions[original_motion.digest] = original_motion

        logger.debug("モーション設定")

        self.output_motion_ctrl.data = VmdMotion(self.output_motion_ctrl.path)

        logger.debug("出力モーション生成")

        if not (self.model_ctrl.data and self.motion_ctrl.data):
            logger.warning("モデルデータもしくはモーションデータが正常に配置できませんでした", decoration=MLogger.Decoration.BOX)
            return

        self.frame_slider.SetMaxFrameNo(motion.max_fno)
        logger.debug("SetMaxFrameNo")

        self.bone_matrixes = bone_matrixes
        logger.debug("bone_matrixes")

        self.blink_conditions = blink_conditions
        logger.debug("blink_conditions")

        self.canvas.append_model_set(self.model_ctrl.data, self.motion_ctrl.data, bone_alpha=0.0)
        self.canvas.Refresh()

        self.Enable(False)
        self.EnableExec(True)

    def exec(self, event: wx.Event) -> None:
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.frame.running_worker = True
        self.Enable(False)
        self.service_worker.start()

    def on_exec_result(self, result: bool, data: tuple[VmdMotion, VmdMotion, list[int]], elapsed_time: str):
        self.frame.running_worker = False
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        # モーションデータを上書きして再読み込み
        motion, output_motion, fnos = data
        self.motion_ctrl.data = motion
        self.canvas.model_sets[0].motion = motion
        self.output_motion_ctrl.data = output_motion
        # 関連ボーン・モーフのキーがある箇所に飛ぶ
        self.frame_slider.SetKeyFrames(list(range(motion.max_fno + 1)))
        if 1 < len(fnos):
            self.frame_slider.SetKeyFrames(fnos)
        else:
            key_fnos = [fno for bone_name in self.key_names for fno in output_motion.bones[bone_name].indexes]
            if key_fnos:
                self.frame_slider.SetKeyFrames(sorted(set(key_fnos)))

        self.on_frame_change(wx.EVT_BUTTON)

        # 保存ボタンを有効にできるようにする
        self.enabled_save = True
        self.Enable(True)
        self.frame.on_sound()

    def save(self, event: wx.Event) -> None:
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.frame.running_worker = True
        self.Enable(False)
        self.save_worker.start()

    def on_save_result(self, result: bool, data: Optional[Any], elapsed_time: str) -> None:
        self.frame.running_worker = False
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        # 保存ボタンを有効にできるようにする
        self.enabled_save = True
        self.Enable(True)
        self.frame.on_sound()

    def on_change_model_pmx(self, event: wx.Event) -> None:
        self.model_ctrl.unwrap()
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            self.create_output_path()
        self.Enable(False)
        self.EnableLoad(True)

    def on_change_motion(self, event: wx.Event) -> None:
        self.motion_ctrl.unwrap()
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()
            self.create_output_path()
        self.Enable(False)
        self.EnableLoad(True)

    def create_output_path(self) -> None:
        if self.model_ctrl.valid() and self.motion_ctrl.valid():
            model_dir_path, model_file_name, model_file_ext = separate_path(self.model_ctrl.path)
            motion_dir_path, motion_file_name, motion_file_ext = separate_path(self.motion_ctrl.path)
            self.model_ctrl.read_name()
            self.motion_ctrl.read_name()
            self.output_motion_ctrl.path = os.path.join(
                motion_dir_path,
                f"{motion_file_name}_{model_file_name}_{__(self.emotion_type)}_{datetime.now():%Y%m%d_%H%M%S}{motion_file_ext}",
            )

    def Enable(self, enable: bool) -> None:
        self.EnableExec(enable)
        if not enable:
            self.enabled_save = self.save_btn_ctrl.Enabled
            self.save_btn_ctrl.Enable(enable)
        elif self.enabled_save:
            self.save_btn_ctrl.Enable(True)

    def EnableLoad(self, enable: bool) -> None:
        self.model_ctrl.Enable(enable)
        self.motion_ctrl.Enable(enable)
        self.output_motion_ctrl.Enable(enable)
        self.prepare_btn_ctrl.Enable(enable)

    def EnableExec(self, enable: bool) -> None:
        self.EnableLoad(enable)
        self.frame_slider.Enable(enable)
        self.play_ctrl.Enable(enable)
        self.sub_window_ctrl.Enable(enable)
        self.exec_btn_ctrl.Enable(enable)

    def on_frame_change(self, event: wx.Event):
        self.Enable(False)
        self.canvas.change_motion(event, True, 0)
        self.Enable(True)

    @property
    def fno(self) -> int:
        return self.frame_slider.GetValue()

    @fno.setter
    def fno(self, v: int) -> None:
        logger.debug(f"fno setter {v}")
        self.frame_slider.ChangeValue(v)

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

    def on_play(self, event: wx.Event) -> None:
        if self.canvas.playing:
            self.stop_play()
        else:
            self.start_play()
        self.canvas.on_play(event)

    def on_show_sub_window(self, event: wx.Event) -> None:
        self.create_sub_window()

        if self.sub_window:
            if not self.sub_window.IsShown():
                self.sub_window.Show()
            elif self.sub_window.IsShown():
                self.sub_window.Hide()
        event.Skip()

    def create_sub_window(self) -> None:
        model: Optional[PmxModel] = self.model_ctrl.data
        if not self.sub_window and model:
            self.sub_window = SubCanvasWindow(
                self.frame, self.canvas, __("アッププレビュー"), self.sub_window_size, [model.name], [model.bones.names]
            )
            frame_x, frame_y = self.frame.GetPosition()
            self.sub_window.SetPosition(wx.Point(max(0, frame_x - self.sub_window_size.x - 10), max(0, frame_y)))

    def fit_window(self) -> None:
        self.scrolled_window.Layout()
        self.scrolled_window.Fit()
        self.Layout()
