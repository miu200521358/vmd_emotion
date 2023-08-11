import os
from typing import Iterable, Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.utils.file_utils import insert_history, save_histories
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.form.panel.service_panel import ServicePanel
from service.form.widgets.morph_condition_ctrl import MorphConditionCtrl
from service.worker.config.morph_adjust_worker import MorphAdjustWorker

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MorphAdjustPanel(ServicePanel):
    def __init__(self, frame: NotebookFrame, tab_idx: int, *args, **kw) -> None:
        self.conditions: list[MorphConditionCtrl] = []

        super().__init__(frame, tab_idx, *args, **kw)

    @property
    def emotion_type(self) -> str:
        return "モーフ条件調整"

    @property
    def console_rows(self) -> int:
        return 170

    @property
    def key_names(self) -> Iterable[str]:
        return []

    def create_service_worker(self) -> MorphAdjustWorker:
        return MorphAdjustWorker(self.frame, self, self.on_exec_result)

    def _initialize_service_ui_header(self) -> None:
        self.header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_ctrl = wx.Button(self, wx.ID_ANY, __("条件追加"), wx.DefaultPosition, wx.Size(120, -1))
        self.add_ctrl.SetToolTip(__("調整条件を追加できます"))
        self.add_ctrl.Bind(wx.EVT_BUTTON, self.on_add_condition)
        self.header_sizer.Add(self.add_ctrl, 0, wx.ALL, 3)

        self.clear_ctrl = wx.Button(self, wx.ID_ANY, __("条件全削除"), wx.DefaultPosition, wx.Size(120, -1))
        self.clear_ctrl.SetToolTip(__("全ての調整条件を削除できます"))
        self.clear_ctrl.Bind(wx.EVT_BUTTON, self.on_clear_condition)
        self.header_sizer.Add(self.clear_ctrl, 0, wx.ALL, 3)

        self.root_sizer.Add(self.header_sizer, 0, wx.ALL | wx.ALIGN_RIGHT, 3)

    def _initialize_service_ui(self) -> None:
        self.condition_sizer = wx.FlexGridSizer(18)

        # --------------
        self.window_sizer.Add(self.condition_sizer, 0, wx.ALL, 3)

    def Enable(self, enable: bool):
        super().Enable(enable)
        self.add_ctrl.Enable(enable)
        self.clear_ctrl.Enable(enable)
        for condition in self.conditions:
            condition.Enable(enable)

    def on_preparer_result(
        self,
        result: bool,
        data: Optional[tuple[PmxModel, PmxModel, VmdMotion, VmdMotion, dict[str, float], VmdBoneFrameTrees]],
        elapsed_time: str,
    ):
        super().on_preparer_result(result, data, elapsed_time)

        self.on_add_condition(wx.EVT_BUTTON)

    def save_histories_on_exec(self) -> None:
        for condition in self.conditions:
            history = condition.history
            if history:
                insert_history(history, self.frame.histories["morph_condition"])

        save_histories(self.frame.histories)

    def on_add_condition(self, event: wx.Event) -> None:
        self.conditions.append(
            MorphConditionCtrl(self.frame, self, self.window, self.condition_sizer, self.model_ctrl.data, len(self.conditions))
        )
        self.fit_window()

    def on_clear_condition(self, event: wx.Event) -> None:
        self.window_sizer.Hide(self.condition_sizer, recursive=True)
        del self.conditions
        self.conditions = []
