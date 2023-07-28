import os
from typing import Any, Optional

import wx

from mlib.base.logger import ConsoleHandler, MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.service.form.base_frame import BaseFrame
from mlib.utils.file_utils import save_histories
from mlib.vmd.vmd_collection import VmdMotion
from service.form.panel.config_panel import ConfigPanel
from service.form.panel.file_panel import FilePanel
from service.worker.load_worker import LoadWorker
from service.worker.save_worker import SaveWorker
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from mlib.base.math import MVector3D
from service.usecase.load_usecase import DuplicateMorph

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class MainFrame(BaseFrame):
    def __init__(self, app: wx.App, title: str, size: wx.Size, *args, **kw) -> None:
        super().__init__(
            app,
            history_keys=["model_pmx", "motion_vmd"],
            title=title,
            size=size,
        )
        self.selected_tab_idx = 0

        # ファイルタブ
        self.file_panel = FilePanel(self, 0)
        self.notebook.AddPage(self.file_panel, __("ファイル"), False)

        # 設定タブ
        self.config_panel = ConfigPanel(self, 1)
        self.notebook.AddPage(self.config_panel, __("設定"), False)

        # ブレンドタブ（設定パネルはそのまま）
        self.notebook.AddPage(self.config_panel, __("モーフ"), False)

        self.load_worker = LoadWorker(self, self.on_result)
        self.save_worker = SaveWorker(self, self.on_save_result)

        self.file_panel.exec_btn_ctrl.exec_worker = self.save_worker

        MLogger.console_handler = ConsoleHandler(self.file_panel.console_ctrl.text_ctrl)
        MLogger.console_handler2 = ConsoleHandler(self.config_panel.console_ctrl.text_ctrl)

    def on_change_tab(self, event: wx.Event) -> None:
        self.selected_tab_idx = self.notebook.GetSelection()
        self.config_panel.morph_set.bone_weight_check_ctrl.SetValue(0)

        if self.selected_tab_idx in [self.config_panel.tab_idx, self.config_panel.tab_idx + 1]:
            self.notebook.ChangeSelection(self.file_panel.tab_idx)
            if not self.load_worker.started:
                if not self.file_panel.model_ctrl.valid():
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    logger.warning("人物モデル欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return
                if not self.file_panel.motion_ctrl.valid():
                    self.file_panel.exec_btn_ctrl.Enable(False)
                    logger.warning("モーション欄に有効なパスが設定されていない為、タブ遷移を中断します。")
                    return

                if not self.file_panel.model_ctrl.data or not self.file_panel.motion_ctrl.data:
                    # 設定タブにうつった時に読み込む
                    self.config_panel.canvas.clear_model_set()
                    self.save_histories()

                    self.file_panel.Enable(False)
                    self.load_worker.start()
                else:
                    # 既に読み取りが完了していたらそのまま表示
                    if self.selected_tab_idx == self.config_panel.tab_idx:
                        self.config_panel.canvas.model_sets[0].motion = self.file_panel.motion_ctrl.data
                        self.config_panel.canvas.shader.look_at_center = (
                            self.config_panel.canvas.shader.INITIAL_LOOK_AT_CENTER_POSITION.copy()
                        )
                        self.config_panel.canvas.shader.vertical_degrees = self.config_panel.canvas.shader.INITIAL_VERTICAL_DEGREES
                        self.config_panel.canvas.change_motion(event, model_index=0)
                        self.config_panel.canvas.Refresh()

                        self.config_panel.show_config = True
                        self.config_panel.change_window()
                        self.notebook.ChangeSelection(self.config_panel.tab_idx)
                    else:
                        self.config_panel.canvas.model_sets[0].motion = VmdMotion()
                        self.config_panel.canvas.shader.look_at_center = MVector3D(
                            0,
                            (
                                (self.config_panel.bone_matrixes[0, "両目"].position.y + self.config_panel.bone_matrixes[0, "頭"].position.y)
                                / 2
                            ),
                            0,
                        )
                        self.config_panel.canvas.shader.vertical_degrees = 6
                        self.config_panel.canvas.change_motion(event, model_index=0)
                        self.config_panel.canvas.Refresh()

                        self.config_panel.show_config = False
                        self.config_panel.change_window()
                        self.notebook.ChangeSelection(self.config_panel.tab_idx + 1)
        else:
            self.selected_tab_idx = self.file_panel.tab_idx
            self.notebook.ChangeSelection(self.file_panel.tab_idx)

    def save_histories(self) -> None:
        self.file_panel.model_ctrl.save_path()
        self.file_panel.motion_ctrl.save_path()

        save_histories(self.histories)

    def on_result(
        self,
        result: bool,
        data: Optional[
            tuple[
                PmxModel,
                PmxModel,
                VmdMotion,
                VmdMotion,
                dict[str, float],
                VmdBoneFrameTrees,
                dict[tuple[int, int], DuplicateMorph],
            ]
        ],
        elapsed_time: str,
    ) -> None:
        self.file_panel.console_ctrl.write(f"\n----------------\n{elapsed_time}")

        if not (result and data):
            self.file_panel.Enable(True)
            self.file_panel.exec_btn_ctrl.Enable(False)
            self.on_sound()
            return

        logger.info("描画準備開始", decoration=MLogger.Decoration.BOX)

        original_model, model, original_motion, motion, blink_conditions, bone_matrixes, morph_duplicate_choices = data

        self.file_panel.model_ctrl.original_data = original_model
        self.file_panel.model_ctrl.data = model
        self.file_panel.motion_ctrl.original_data = original_motion
        self.file_panel.motion_ctrl.data = motion
        self.file_panel.exec_btn_ctrl.Enable(True)
        self.file_panel.output_motion_ctrl.data = VmdMotion(self.file_panel.output_motion_ctrl.path)

        if not (self.file_panel.model_ctrl.data and self.file_panel.motion_ctrl.data):
            return

        # キーフレを戻す
        self.config_panel.fno = 0
        # まばたき条件の初期化
        self.config_panel.blink_set.initialize(blink_conditions)
        self.config_panel.frame_slider.SetMaxFrameNo(motion.max_fno)
        self.config_panel.bone_matrixes = bone_matrixes

        try:
            logger.info("モデル描画準備")

            if self.selected_tab_idx == self.config_panel.tab_idx:
                self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, self.file_panel.motion_ctrl.data, bone_alpha=0.0)
                self.config_panel.canvas.Refresh()

                self.config_panel.show_config = True
                self.config_panel.change_window()
                self.notebook.ChangeSelection(self.config_panel.tab_idx)
            else:
                self.config_panel.canvas.append_model_set(self.file_panel.model_ctrl.data, VmdMotion(), bone_alpha=0.0)
                self.config_panel.canvas.shader.look_at_center = MVector3D(
                    0, ((bone_matrixes[0, "両目"].position.y + bone_matrixes[0, "頭"].position.y) / 2), 0
                )
                self.config_panel.canvas.shader.vertical_degrees = 6
                self.config_panel.canvas.Refresh()

                self.config_panel.show_config = False
                self.config_panel.change_window()
                self.notebook.ChangeSelection(self.config_panel.tab_idx + 1)
        except:
            logger.critical("モデル描画初期化処理失敗")

        self.config_panel.morph_set.initialize(morph_duplicate_choices)

        self.file_panel.Enable(True)
        self.on_sound()

    def on_exec(self) -> None:
        self.save_worker.start()

    def on_save_result(self, result: bool, data: Optional[Any], elapsed_time: str) -> None:
        self.file_panel.Enable(True)
        self.on_sound()

    def show_bone_weight(self, is_show_bone_weight: bool) -> None:
        self.config_panel.canvas.animations[0].is_show_bone_weight = is_show_bone_weight
        self.config_panel.canvas.Refresh()
