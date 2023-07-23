import os

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class GazeUsecase:
    def create_gaze(self, model: PmxModel, motion: VmdMotion) -> None:
        """視線生成"""

        if "両目" in motion.bones.names:
            # 既存の両目キーフレは削除
            del motion.bones["両目"]
