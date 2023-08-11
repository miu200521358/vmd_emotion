import os
from typing import Optional

import wx

from mlib.core.logger import MLogger
from mlib.pmx.canvas import SyncSubCanvasWindow
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.base_panel import BasePanel
from mlib.service.form.notebook_frame import NotebookFrame
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.blink_panel import BlinkPanel
from service.form.panel.gaze_panel import GazePanel
from service.form.panel.morph_adjust_panel import MorphAdjustPanel
from service.form.panel.repair_panel import RepairPanel
from service.form.widgets.bezier_dialog import BezierDialog
from service.form.widgets.morph_condition_ctrl import MorphConditionCtrl
from service.form.widgets.morph_sub_window import MorphSubCanvasWindow

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MainFrame(NotebookFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw) -> None:
        super().__init__(
            app,
            history_keys=["model_pmx", "motion_vmd", "morph_condition"],
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

        self.morph_sub_window_size = wx.Size(300, 400)
        self.morph_sub_window: Optional[MorphSubCanvasWindow] = None

        self.sync_sub_window_size = wx.Size(300, 300)
        self.sync_sub_window: Optional[SyncSubCanvasWindow] = None

        self.bezier_dialog_size = wx.Size(300, 700)
        self.bezier_dialog: Optional[BezierDialog] = None

    def show_morph_sub_window(self, event: wx.Event, panel: BasePanel) -> None:
        self.create_morph_sub_window(panel)

        if self.morph_sub_window:
            if self.sync_sub_window and self.sync_sub_window.IsShown():
                self.sync_sub_window.Hide()

            if self.bezier_dialog and self.bezier_dialog.IsShown():
                self.bezier_dialog.Hide()

            if not self.morph_sub_window.IsShown():
                model: Optional[PmxModel] = panel.model_ctrl.data
                if model:
                    self.morph_sub_window.panel.canvas.clear_model_set()
                    self.morph_sub_window.panel.canvas.append_model_set(model, VmdMotion(), bone_alpha=0.0, is_sub=True)
                    self.morph_sub_window.panel.canvas.vertical_degrees = 5
                    self.morph_sub_window.panel.canvas.look_at_center = model.bones["頭"].position.copy()
                    self.morph_sub_window.panel.canvas.Refresh()

                frame_x, frame_y = self.GetPosition()
                self.morph_sub_window.SetPosition(wx.Point(max(0, frame_x + self.GetSize().GetWidth() + 10), max(0, frame_y + 30)))

                self.morph_sub_window.Show()
            elif self.morph_sub_window.IsShown():
                self.morph_sub_window.Hide()
        event.Skip()

    def create_morph_sub_window(self, panel: BasePanel) -> None:
        model: Optional[PmxModel] = panel.model_ctrl.data
        if not self.morph_sub_window and model:
            self.morph_sub_window = MorphSubCanvasWindow(
                self, __("モーフプレビュー"), self.morph_sub_window_size, [model.name], [model.bones.names], model.morphs.names
            )

    def show_sync_sub_window(self, event: wx.Event, panel: BasePanel) -> None:
        self.create_sync_sub_window(panel)

        if self.sync_sub_window:
            if self.morph_sub_window and self.morph_sub_window.IsShown():
                self.morph_sub_window.Hide()

            if self.bezier_dialog and self.bezier_dialog.IsShown():
                self.bezier_dialog.Hide()

            if not self.sync_sub_window.IsShown():
                model: Optional[PmxModel] = panel.model_ctrl.data
                if model:
                    self.sync_sub_window.panel.canvas.clear_model_set()
                    self.sync_sub_window.panel.canvas.append_model_set(model, VmdMotion(), bone_alpha=0.0, is_sub=True)
                    self.sync_sub_window.panel.canvas.Refresh()

                frame_x, frame_y = self.GetPosition()
                self.sync_sub_window.SetPosition(wx.Point(max(0, frame_x - self.sync_sub_window_size.x - 10), max(0, frame_y)))

                self.sync_sub_window.Show()
            elif self.sync_sub_window.IsShown():
                self.sync_sub_window.Hide()
        event.Skip()

    def create_sync_sub_window(self, panel: BasePanel) -> None:
        model: Optional[PmxModel] = panel.model_ctrl.data
        if not self.sync_sub_window and model:
            self.sync_sub_window = SyncSubCanvasWindow(
                self, panel.canvas, __("アッププレビュー"), self.sync_sub_window_size, [model.name], [model.bones.names]
            )

    def on_change_tab(self, event: wx.Event) -> None:
        if self.running_worker:
            # 処理が動いている場合、動かさない
            self.notebook.ChangeSelection(self.selected_tab_idx)
            event.Skip()
            return

        # 処理が終わっている場合、動かしてOK
        self.selected_tab_idx = self.notebook.GetSelection()

    def show_bezier_dialog(self, event: wx.Event, panel: BasePanel, condition: MorphConditionCtrl) -> None:
        self.Enable(False)
        self.create_bezier_dialog(panel, condition)

        if self.bezier_dialog:
            if self.sync_sub_window and self.sync_sub_window.IsShown():
                self.sync_sub_window.Hide()

            if self.morph_sub_window and self.morph_sub_window.IsShown():
                self.morph_sub_window.Hide()

            if not self.bezier_dialog.IsShown():
                self.bezier_dialog.bezier_panel.bezier_ctrl.start_x_ctrl.SetValue(condition.start_x_ctrl.GetValue())
                self.bezier_dialog.bezier_panel.bezier_ctrl.start_y_ctrl.SetValue(condition.start_y_ctrl.GetValue())
                self.bezier_dialog.bezier_panel.bezier_ctrl.end_x_ctrl.SetValue(condition.end_x_ctrl.GetValue())
                self.bezier_dialog.bezier_panel.bezier_ctrl.end_y_ctrl.SetValue(condition.end_y_ctrl.GetValue())
                self.bezier_dialog.bezier_panel.slider.SetValue(0.0)

                self.bezier_dialog.bezier_panel.canvas.clear_model_set()
                self.bezier_dialog.bezier_panel.canvas.append_model_set(panel.model_ctrl.data, VmdMotion(), bone_alpha=0.0, is_sub=True)
                self.bezier_dialog.bezier_panel.canvas.vertical_degrees = 5
                self.bezier_dialog.bezier_panel.canvas.look_at_center = panel.model_ctrl.data.bones["頭"].position.copy()
                self.bezier_dialog.bezier_panel.canvas.Refresh()

                frame_x, frame_y = self.GetPosition()
                self.bezier_dialog.SetPosition(wx.Point(max(0, frame_x + self.GetSize().GetWidth() + 10), max(0, frame_y + 30)))

                self.bezier_dialog.ShowModal()

            elif self.bezier_dialog.IsShown():
                self.bezier_dialog.Hide()
        self.Enable(True)
        event.Skip()

    def create_bezier_dialog(self, panel: BasePanel, condition: MorphConditionCtrl) -> None:
        if not self.bezier_dialog:
            self.bezier_dialog = BezierDialog(self, condition, __("補間曲線プレビュー"), self.bezier_dialog_size)
