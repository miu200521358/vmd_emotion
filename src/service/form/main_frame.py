import os

import wx

from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.gaze_panel import GazePanel
from service.form.panel.blink_panel import BlinkPanel
from service.form.panel.repair_panel import RepairPanel
from service.form.panel.morph_adjust_panel import MorphAdjustPanel

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MainFrame(NotebookFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw) -> None:
        super().__init__(
            app,
            history_keys=["model_pmx", "motion_vmd"],
            title=title,
            size=size,
        )
        self.selected_tab_idx = 0
        self.running_worker = False

        # 目線生成
        self.gaze_panel = GazePanel(self, 0)
        self.notebook.AddPage(self.gaze_panel, __("目線生成"), True)

        # まばたき生成
        self.blink_panel = BlinkPanel(self, 1)
        self.notebook.AddPage(self.blink_panel, __("まばたき生成"), False)

        # 破綻補正
        self.repair_panel = RepairPanel(self, 2)
        self.notebook.AddPage(self.repair_panel, __("破綻補正"), False)

        # モーフ条件調整
        self.morph_adjust_panel = MorphAdjustPanel(self, 3)
        self.notebook.AddPage(self.morph_adjust_panel, __("モーフ条件調整"), False)

        self.models: dict[str, PmxModel] = {}
        self.motions: dict[str, VmdMotion] = {}

    def on_change_tab(self, event: wx.Event) -> None:
        if self.running_worker:
            # 処理が動いている場合、動かさない
            self.notebook.ChangeSelection(self.selected_tab_idx)
            event.Skip()
            return

        # 処理が終わっている場合、動かしてOK
        self.selected_tab_idx = self.notebook.GetSelection()
