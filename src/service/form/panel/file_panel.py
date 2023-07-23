import os
from datetime import datetime

import wx

from mlib.base.logger import MLogger
from mlib.service.form.base_frame import BaseFrame
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.widgets.console_ctrl import ConsoleCtrl
from mlib.service.form.widgets.exec_btn_ctrl import ExecButton
from mlib.service.form.widgets.file_ctrl import MPmxFilePickerCtrl, MVmdFilePickerCtrl
from mlib.utils.file_utils import separate_path

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class FilePanel(BasePanel):
    def __init__(self, frame: BaseFrame, tab_idx: int, *args, **kw) -> None:
        super().__init__(frame, tab_idx, *args, **kw)

        self._initialize_ui()

    def _initialize_ui(self) -> None:
        self.model_ctrl = MPmxFilePickerCtrl(
            self.frame,
            self,
            key="model_pmx",
            title="人物モデル",
            is_show_name=True,
            name_spacer=3,
            is_save=False,
            tooltip="お着替えさせたい対象の人物モデルを指定してください",
            file_change_event=self.on_change_model_pmx,
        )
        self.model_ctrl.set_parent_sizer(self.root_sizer)

        self.motion_ctrl = MVmdFilePickerCtrl(
            self.frame,
            self,
            key="motion_vmd",
            title="表示モーション",
            is_show_name=True,
            name_spacer=1,
            is_save=False,
            tooltip="任意でVMDモーションデータを指定する事ができます\n空欄の場合、人物と衣装は初期状態で表示します",
            file_change_event=self.on_change_motion,
        )
        self.motion_ctrl.set_parent_sizer(self.root_sizer)

        self.output_motion_ctrl = MVmdFilePickerCtrl(
            self.frame,
            self,
            title="表情モーション出力先",
            is_show_name=False,
            is_save=True,
            tooltip="表情モーションの出力ファイルパスです\n任意の値に変更可能です",
        )
        self.output_motion_ctrl.set_parent_sizer(self.root_sizer)

        self.exec_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.exec_btn_ctrl = ExecButton(
            self,
            __("表情モーション出力"),
            __("表情モーション出力停止"),
            self.exec,
            250,
            __("生成した表情のみをVMDモーションデータとして出力します\n読み込み結果を設定タブで確認した後にクリックできるようになります"),
        )
        # 初期では無効化
        self.exec_btn_ctrl.Enable(False)
        self.exec_btn_sizer.Add(self.exec_btn_ctrl, 0, wx.ALL, 3)
        self.root_sizer.Add(self.exec_btn_sizer, 0, wx.ALIGN_CENTER | wx.SHAPED, 5)

        self.console_ctrl = ConsoleCtrl(self.frame, self, rows=550)
        self.console_ctrl.set_parent_sizer(self.root_sizer)

        self.root_sizer.Add(wx.StaticLine(self, wx.ID_ANY), wx.GROW)

    def exec(self, event: wx.Event) -> None:
        self.frame.on_exec()

    def on_change_model_pmx(self, event: wx.Event) -> None:
        self.model_ctrl.unwrap()
        if self.model_ctrl.read_name():
            self.model_ctrl.read_digest()
            self.create_output_path()
        self.exec_btn_ctrl.Enable(False)

    def on_change_motion(self, event: wx.Event) -> None:
        self.motion_ctrl.unwrap()
        if self.motion_ctrl.read_name():
            self.motion_ctrl.read_digest()
            self.create_output_path()
        self.exec_btn_ctrl.Enable(False)

    def create_output_path(self) -> None:
        if self.model_ctrl.valid() and self.motion_ctrl.valid():
            model_dir_path, model_file_name, model_file_ext = separate_path(self.model_ctrl.path)
            motion_dir_path, motion_file_name, motion_file_ext = separate_path(self.motion_ctrl.path)
            self.model_ctrl.read_name()
            self.motion_ctrl.read_name()
            self.output_motion_ctrl.path = os.path.join(
                motion_dir_path,
                f"{motion_file_name}_Emotion_{model_file_name}_{datetime.now():%Y%m%d_%H%M%S}{motion_file_ext}",
            )

    def Enable(self, enable: bool) -> None:
        self.model_ctrl.Enable(enable)
        self.motion_ctrl.Enable(enable)
        self.output_motion_ctrl.Enable(enable)
