import os

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadUsecase:
    def valid_model(self, model: PmxModel) -> None:
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
        missing_bone_names = sorted(list(required_bone_names - set(model.bones.names)))
        if missing_bone_names:
            raise MApplicationException(
                "モデルの表情生成に必要なボーンが不足しています。\n不足ボーン: {b}",
                b=", ".join(missing_bone_names),
            )

    def valid_motion(self, original_motion: VmdMotion) -> VmdMotion:
        """モーフ生成にあったモーションを取得する"""
        motion = original_motion.copy()

        if "両目" in motion.bones.names:
            logger.warning("モーションに両目キーフレームが存在しているため、除外して表情を生成します", decoration=MLogger.Decoration.BOX)
            del motion.bones["両目"]

        return motion
