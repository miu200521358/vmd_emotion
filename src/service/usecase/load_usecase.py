import os

from mlib.core.exception import MApplicationException
from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.usecase.config.blink_usecase import BLINK_CONDITIONS

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadUsecase:
    def valid_model(self, original_model: PmxModel) -> PmxModel:
        """モーフ生成に最低限必要なボーンで不足しているボーンリストを取得する"""
        required_bone_names = {
            "センター",
            "上半身",
            "首",
            "頭",
            "左目",
            "右目",
            "両目",
        }
        missing_bone_names = sorted(list(required_bone_names - set(original_model.bones.names)))
        if missing_bone_names:
            raise MApplicationException(
                "モデルの表情生成に必要なボーンが不足しています。\n不足ボーン: {b}",
                b=", ".join(missing_bone_names),
            )

        return original_model.copy()

    def valid_motion(self, original_motion: VmdMotion) -> VmdMotion:
        """モーフ生成にあったモーションを取得する"""
        motion = original_motion.copy()

        return motion

    def get_bone_matrixes(self, model: PmxModel) -> VmdBoneFrameTrees:
        """初期姿勢での各ボーンの位置を求める"""
        bone_matrixes = VmdMotion().animate_bone([0], model)
        return bone_matrixes

    def get_blink_conditions(self) -> dict[str, float]:
        return BLINK_CONDITIONS
