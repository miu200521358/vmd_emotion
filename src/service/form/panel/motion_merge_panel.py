import os
from datetime import datetime
from typing import Iterable

import wx

from mlib.core.logger import MLogger
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.exec_btn_ctrl import ExecButton
from mlib.service.form.widgets.file_ctrl import MVmdFilePickerCtrl
from mlib.utils.file_utils import save_histories, separate_path
from service.form.panel.service_panel import ServicePanel
from service.worker.config.motion_merge_worker import MotionMergeWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MotionMergePanel(ServicePanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        self.motions: list[MVmdFilePickerCtrl] = []

        super().__init__(frame, tab_idx, *args, **kw)

        self.on_add_motion(wx.EVT_BUTTON)

    @property
    def emotion_type(self) -> str:
        return "モーション統合"

    @property
    def console_rows(self) -> int:
        return 170

    @property
    def key_names(self) -> Iterable[str]:
        return []

    def create_service_worker(self) -> MotionMergeWorker:
        return MotionMergeWorker(self.frame, self, self.on_exec_result)

    def _initialize_ui(self) -> None:
        self.header_sizer = wx.BoxSizer(wx.VERTICAL)

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

        self.file_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.output_motion_ctrl = MVmdFilePickerCtrl(
            self,
            self.frame,
            self,
            title="統合モーション出力先",
            is_show_name=False,
            is_save=True,
            tooltip="統合モーションの出力ファイルパスです\n任意の値に変更可能です",
        )
        self.output_motion_ctrl.set_parent_sizer(self.file_sizer)

        self.root_sizer.Add(self.file_sizer, 0, wx.ALL | wx.EXPAND, 3)

        # ボタン -------------------------
        self._create_button_set()

        # コンソール -----------------
        self.console_ctrl = ConsoleCtrl(self, self.frame, self, rows=self.console_rows)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

    def _initialize_service_ui_header(self) -> None:
        self.header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_ctrl = wx.Button(self, wx.ID_ANY, __("統合モーション追加"), wx.DefaultPosition, wx.Size(120, -1))
        self.add_ctrl.SetToolTip(__("統合対象モーションを追加できます"))
        self.add_ctrl.Bind(wx.EVT_BUTTON, self.on_add_motion)
        self.header_sizer.Add(self.add_ctrl, 0, wx.ALL, 3)

        self.clear_ctrl = wx.Button(self, wx.ID_ANY, __("統合モーション全削除"), wx.DefaultPosition, wx.Size(120, -1))
        self.clear_ctrl.SetToolTip(__("全ての統合対象モーションを削除できます"))
        self.clear_ctrl.Bind(wx.EVT_BUTTON, self.on_clear_motion)
        self.header_sizer.Add(self.clear_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.header_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 3)

    def _initialize_service_ui(self) -> None:
        # 個別サービス ---------------------------
        self.motion_sizer = wx.BoxSizer(wx.VERTICAL)

        self.window_sizer.Add(self.motion_sizer, 0, wx.ALL | wx.EXPAND, 3)

    def _create_button_set(self) -> None:
        self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.exec_btn_ctrl = ExecButton(
            self,
            self,
            __(f"{self.exec_label}"),
            __(f"{self.exec_label}停止"),
            self.exec,
            250,
            __("統合モーションをVMDモーションデータとして出力します\nモーションを1件でも指定した後、クリックできるようになります"),
        )
        self.btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 3)

    def Enable(self, enable: bool):
        super().Enable(enable)
        self.add_ctrl.Enable(enable)
        self.clear_ctrl.Enable(enable)
        for condition in self.motions:
            condition.Enable(enable)
        # 統合可能なモーションが2件以上あれば保存可能
        if self.exec_btn_ctrl:
            self.exec_btn_ctrl.Enable(1 < len([motion_ctrl for motion_ctrl in self.motions if motion_ctrl.valid()]))

    def save_histories_on_exec(self) -> None:
        for motion_ctrl in self.motions:
            motion_ctrl.save_path()

        save_histories(self.frame.histories)

    def on_add_motion(self, event: wx.Event) -> None:
        target_idx = len(self.motions)
        motion_ctrl = MVmdFilePickerCtrl(
            self.window,
            self.frame,
            self,
            key="motion_vmd",
            title="統合対象モーション",
            is_show_name=True,
            name_spacer=1,
            is_save=False,
            tooltip="統合したいモーションを指定してください",
            file_change_event=lambda event: self.on_change_motion(event, target_idx),
        )
        self.motions.append(motion_ctrl)
        motion_ctrl.set_parent_sizer(self.motion_sizer)
        self.Enable(True)
        self.fit_window()

    def on_change_motion(self, event: wx.Event, target_idx: int) -> None:
        self.motions[target_idx].unwrap()
        if self.motions[target_idx].read_name():
            self.motions[target_idx].read_digest()
            self.create_output_path()

        self.on_add_motion(event)

    def create_output_path(self) -> None:
        if 1 > len(self.motions) or not self.motions[0].valid():
            return

        motion_dir_path, motion_file_name, motion_file_ext = separate_path(self.motions[0].path)
        self.output_motion_ctrl.path = os.path.join(
            motion_dir_path,
            f"{motion_file_name}_{__('統合')}_{datetime.now():%Y%m%d_%H%M%S}{motion_file_ext}",
        )

    def on_clear_motion(self, event: wx.Event) -> None:
        self.window_sizer.Hide(self.motion_sizer, recursive=True)
        del self.motions
        self.motions = []
