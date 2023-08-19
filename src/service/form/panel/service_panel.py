import os
from datetime import datetime
from typing import Iterable, Optional

import wx

from mlib.core.logger import ConsoleHandler, MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.base_worker import BaseWorker
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.service.form.notebook_panel import NotebookPanel
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.exec_btn_ctrl import ExecButton
from mlib.service.form.widgets.file_ctrl import MPmxFilePickerCtrl, MVmdFilePickerCtrl
from mlib.utils.file_utils import save_histories, separate_path
from mlib.vmd.vmd_collection import VmdMotion
from service.worker.load_worker import LoadWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class ServicePanel(NotebookPanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, *args, **kw)

        self.load_worker = LoadWorker(frame, self, self.on_preparer_result)
        self.load_worker.panel = self

        self.service_worker = self.create_service_worker()

        self.model_ctrl: Optional[MPmxFilePickerCtrl] = None
        self.motion_ctrl: Optional[MVmdFilePickerCtrl] = None
        self.prepare_btn_ctrl: Optional[ExecButton] = None
        self.exec_btn_ctrl: Optional[ExecButton] = None

        self._initialize_ui()

        self.fit_window()

        # 初期状態は一旦非活性
        self.Enable(False)

        # 初期状態でファイル系と読み込みボタンは有効
        self.EnableLoad(True)

    @property
    def emotion_type(self) -> str:
        return "表情"

    @property
    def exec_label(self) -> str:
        return f"{self.emotion_type}出力"

    @property
    def console_rows(self) -> int:
        return 100

    @property
    def key_names(self) -> Iterable[str]:
        return []

    def create_service_worker(self) -> BaseWorker:
        return BaseWorker(self.frame, self.on_exec_result)

    def _create_file_set(self) -> None:
        self.model_ctrl = MPmxFilePickerCtrl(
            self,
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
        self.model_ctrl.set_parent_sizer(self.header_sizer)

        self.motion_ctrl = MVmdFilePickerCtrl(
            self,
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
        self.motion_ctrl.set_parent_sizer(self.header_sizer)

        self.output_motion_ctrl = MVmdFilePickerCtrl(
            self,
            self.frame,
            self,
            title=f"{self.emotion_type}モーション出力先",
            is_show_name=False,
            is_save=True,
            tooltip=f"{self.emotion_type}モーションの出力ファイルパスです\n任意の値に変更可能です",
        )
        self.output_motion_ctrl.set_parent_sizer(self.header_sizer)

        self.root_sizer.Add(self.header_sizer, 0, wx.ALL | wx.EXPAND, 3)

    def _create_button_set(self) -> None:
        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.prepare_btn_ctrl = ExecButton(
            self,
            self,
            __("データ読み込み"),
            __("データ読み込み停止"),
            self.prepare,
            250,
            __("指定されたモデルとモーションを読み込みます。"),
        )
        self.btn_sizer.Add(self.prepare_btn_ctrl, 0, wx.ALL, 3)

        self.exec_btn_ctrl = ExecButton(
            self,
            self,
            __(f"{self.exec_label}"),
            __(f"{self.exec_label}停止"),
            self.exec,
            250,
            __(f"生成した{self.emotion_type}をVMDモーションデータとして出力します\nデータ読み込み後、クリックできるようになります"),
        )
        self.btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 3)

    def _initialize_ui(self) -> None:
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

        # ファイル -------------------------

        self._create_file_set()

        # ボタン -------------------------

        self._create_button_set()

        # 個別サービス用ヘッダを追加
        self._initialize_service_ui_header()

        # 個別サービス ---------------------------
        self.window = wx.ScrolledWindow(
            self,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.Size(-1, -1),
            wx.FULL_REPAINT_ON_RESIZE | wx.VSCROLL | wx.HSCROLL,
        )
        self.window.SetScrollRate(5, 5)

        self.window_sizer = wx.BoxSizer(wx.VERTICAL)

        # 個別サービス用UIを追加
        self._initialize_service_ui()

        self.window.SetSizer(self.window_sizer)
        self.root_sizer.Add(self.window, 1, wx.ALL | wx.EXPAND | wx.FIXED_MINSIZE, 3)

        # コンソール -----------------
        self.console_ctrl = ConsoleCtrl(self, self.frame, self, rows=self.console_rows)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

    def _initialize_service_ui_header(self) -> None:
        pass

    def _initialize_service_ui(self) -> None:
        pass

    def prepare(self, event: wx.Event) -> None:
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)

        if not self.load_worker.started:
            if self.model_ctrl and not self.model_ctrl.valid():
                self.Enable(False)
                self.EnableLoad(True)

                logger.warning("人物モデル欄に有効なパスが設定されていない為、読み込みを中断します。")
                return
            if self.motion_ctrl and not self.motion_ctrl.valid():
                self.Enable(False)
                self.EnableLoad(True)

                logger.warning("モーション欄に有効なパスが設定されていない為、読み込みを中断します。")
                return

            if self.model_ctrl and self.motion_ctrl and (not self.model_ctrl.data or not self.motion_ctrl.data):
                # 読み込む
                self.save_histories()

                self.frame.running_worker = True
                self.Enable(False)
                self.EnableLoad(True)
                self.load_worker.start()

    def on_preparer_result(
        self,
        result: bool,
        data: Optional[tuple[PmxModel, PmxModel, VmdMotion, VmdMotion, dict[str, float]]],
        elapsed_time: str,
    ):
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.frame.running_worker = False
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data and self.model_ctrl and self.motion_ctrl):
            self.Enable(False)
            self.EnableLoad(True)
            self.frame.on_sound()
            return

        original_model, model, original_motion, motion, blink_conditions = data

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

        self.blink_conditions = blink_conditions
        logger.debug("blink_conditions")

        self.Enable(False)
        self.EnableExec(True)

        self.frame.on_sound()

        logger.info("読み込み完了", decoration=MLogger.Decoration.BOX)

    def save_histories(self) -> None:
        if self.model_ctrl:
            self.model_ctrl.save_path()
        if self.motion_ctrl:
            self.motion_ctrl.save_path()

        save_histories(self.frame.histories)

    def save_histories_on_exec(self) -> None:
        pass

    def exec(self, event: wx.Event) -> None:
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.frame.running_worker = True
        self.Enable(False)
        if self.exec_btn_ctrl:
            self.exec_btn_ctrl.Enable(True)
        self.save_histories_on_exec()
        self.service_worker.start()

    def on_exec_result(self, result: bool, data: tuple[VmdMotion, VmdMotion, list[int]], elapsed_time: str):
        self.frame.running_worker = False
        MLogger.console_handler = ConsoleHandler(self.console_ctrl.text_ctrl)
        self.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.Enable(True)
            self.frame.on_sound()
            return

        # モーションデータを上書きして再読み込み
        motion, output_motion, fnos = data
        if self.motion_ctrl:
            self.motion_ctrl.data = motion
        self.output_motion_ctrl.data = output_motion

        # 保存ボタンを有効にできるようにする
        self.enabled_save = True
        self.Enable(True)
        self.frame.on_sound()

        logger.info("実行完了", decoration=MLogger.Decoration.BOX)

    def on_change_model_pmx(self, event: wx.Event) -> None:
        if not self.model_ctrl:
            return

        self.model_ctrl.unwrap()
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            self.create_output_path()
        self.Enable(False)
        self.EnableLoad(True)

    def on_change_motion(self, event: wx.Event) -> None:
        if not self.motion_ctrl:
            return

        self.motion_ctrl.unwrap()
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()
            self.create_output_path()
        self.Enable(False)
        self.EnableLoad(True)

    def create_output_path(self) -> None:
        if self.model_ctrl and self.motion_ctrl and self.model_ctrl.valid() and self.motion_ctrl.valid():
            model_dir_path, model_file_name, model_file_ext = separate_path(self.model_ctrl.path)
            motion_dir_path, motion_file_name, motion_file_ext = separate_path(self.motion_ctrl.path)
            motion_file_names = motion_file_name.split("_")
            self.model_ctrl.read_name()
            self.motion_ctrl.read_name()
            if model_file_name in self.motion_ctrl.path and 3 < len(motion_file_names):
                # 既にモデル名が設定済みである場合、モデル名は追加しない
                self.output_motion_ctrl.path = os.path.join(
                    motion_dir_path,
                    f"{'_'.join(motion_file_names[:-3])}_{motion_file_names[-3]}_{__(self.emotion_type)}_"
                    + f"{datetime.now():%Y%m%d_%H%M%S}{motion_file_ext}",
                )
            else:
                self.output_motion_ctrl.path = os.path.join(
                    motion_dir_path,
                    f"{motion_file_name}_{model_file_name}_{__(self.emotion_type)}_{datetime.now():%Y%m%d_%H%M%S}{motion_file_ext}",
                )

    def Enable(self, enable: bool) -> None:
        self.EnableExec(enable)

    def EnableLoad(self, enable: bool) -> None:
        if self.model_ctrl:
            self.model_ctrl.Enable(enable)
        if self.motion_ctrl:
            self.motion_ctrl.Enable(enable)
        self.output_motion_ctrl.Enable(enable)
        if self.prepare_btn_ctrl:
            self.prepare_btn_ctrl.Enable(enable)

    def EnableExec(self, enable: bool) -> None:
        self.EnableLoad(enable)
        if self.exec_btn_ctrl:
            self.exec_btn_ctrl.Enable(enable)

    def on_show_async_window(self, event: wx.Event) -> None:
        self.frame.show_async_sub_window(event, self)

    def on_show_sync_window(self, event: wx.Event) -> None:
        self.frame.show_sync_sub_window(event, self)

    def fit_window(self) -> None:
        self.window.Layout()
        self.window.Fit()
        self.Layout()
