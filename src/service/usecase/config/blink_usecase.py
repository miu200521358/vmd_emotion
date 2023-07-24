from enum import Enum
import os

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.base.math import MVector3D
from mlib.vmd.vmd_part import VmdBoneFrame
from mlib.base.interpolation import get_infections
from mlib.base.math import MQuaternion

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class BlinkUsecase:
    def create_blink(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        condition_probabilities: dict[str, float],
    ) -> None:
        """まばたき生成"""

        if "右目" in motion.bones.names:
            # 既存の両目キーフレは削除
            del motion.bones["右目"]

        if "左目" in motion.bones.names:
            # 既存の両目キーフレは削除
            del motion.bones["左目"]

        if "まばたき" in motion.morphs.names:
            # 既存の両目キーフレは削除
            del motion.morphs["まばたき"]

        # まばたきをする可能性があるキーフレ一覧
        eye_fnos = sorted(set([bf.index for bone_name in model.bone_trees["両目"].names for bf in motion.bones[bone_name]]))

        logger.info("目線変動量取得", decoration=MLogger.Decoration.LINE)
        eye_matrixes = motion.animate_bone(eye_fnos, model, ["両目"], out_fno_log=True)

        prev_blink = None
        blink_vectors: list[MVector3D] = []
        blink_dots: list[float] = []
        for fidx, fno in enumerate(eye_fnos):
            logger.count("目線変動量取得", index=fidx, total_index_count=len(eye_fnos), display_block=100)
            eye_global_direction_vector = eye_matrixes[fno, "両目"].global_matrix * MVector3D(0, 0, -1)
            eye_vector = (eye_global_direction_vector - eye_matrixes[fno, "両目"].position).normalized() * -1

            if not prev_blink:
                # 初回はスルー
                prev_blink = eye_vector
                blink_dots.append(1.0)
                continue

            # 両目の向き
            blink_dot = eye_vector.dot(prev_blink)
            logger.debug(f"fno[{fno:04d}], eye[{eye_global_direction_vector}], blink[{eye_vector}], dot[{blink_dot:.3f}]")

            blink_dots.append(blink_dot)
            blink_vectors.append(eye_vector)
            prev_blink = eye_vector

        if 0 < condition_probabilities[BlinkConditions.INTRO.name]:
            logger.info("イントロ抽出", decoration=MLogger.Decoration.LINE)

        # logger.info("まばたき変曲点抽出", decoration=MLogger.Decoration.LINE)
        # # logger.debug(blink_dots)

        # infection_eyes = get_infections(blink_dots, blink_infection * 0.1)
        # # logger.debug(infection_eyes)

        # logger.info("まばたき生成", decoration=MLogger.Decoration.LINE)

        # # 最初は静止
        # start_bf = VmdBoneFrame(eye_fnos[0], "両目")
        # motion.bones["両目"].append(start_bf)
        # output_motion.bones["両目"].append(start_bf.copy())

        # # 最後は静止
        # end_bf = VmdBoneFrame(eye_fnos[-1], "両目")
        # motion.bones["両目"].append(end_bf)
        # output_motion.bones["両目"].append(end_bf.copy())

        # for i, iidx in enumerate(infection_eyes):
        #     logger.count("まばたき生成", index=i, total_index_count=len(infection_eyes), display_block=1000)

        #     if 1 > i:
        #         continue

        #     fno = eye_fnos[iidx - 1]
        #     blink_vector = blink_vectors[iidx - 1]
        #     infection_blink_vector = blink_vectors[iidx]

        #     # まばたきの変動が一定以上であればまばたきを動かす
        #     blink_full_qq = MQuaternion.rotate(blink_vector, infection_blink_vector)
        #     # Zは前向きの捩れになるので捨てる
        #     blink_original_x_qq, blink_original_y_qq, blink_z_qq, _ = blink_full_qq.separate_by_axis(MVector3D(1, 0, 0))

        #     # まばたきの上下運動
        #     x = blink_original_x_qq.to_signed_degrees(MVector3D(0, 0, -1))
        #     # 補正値を求める(初期で少し下げ目にしておく)
        #     correct_x = fitted_x_function(x) * blink_ratio_x - 2
        #     blink_x_qq = MQuaternion.from_axis_angles(blink_original_x_qq.xyz, correct_x)

        #     # まばたきの左右運動
        #     y = blink_original_y_qq.to_signed_degrees(MVector3D(0, 0, -1))
        #     # 補正値を求める
        #     correct_y = fitted_y_function(y) * blink_ratio_y
        #     blink_y_qq = MQuaternion.from_axis_angles(blink_original_y_qq.xyz, correct_y)

        #     blink_qq = blink_x_qq * blink_y_qq

        #     bf = VmdBoneFrame(fno, "両目")
        #     bf.rotation = blink_qq
        #     motion.bones["両目"].append(bf)
        #     output_motion.bones["両目"].append(bf.copy())

        #     logger.debug("まばたき生成[{f}] 向き[{d}] 回転[{r}]", f=fno, d=infection_blink_vector, r=blink_qq.to_euler_degrees_mmd())

        # for i, (iidx, next_iidx) in enumerate(zip(infection_eyes[:-1], infection_eyes[1:])):
        #     logger.count("まばたきクリア", index=i, total_index_count=len(infection_eyes), display_block=100)

        #     fno = eye_fnos[iidx]
        #     next_fno = eye_fnos[next_iidx]

        #     # 前のまばたきとの間に静止期間を設ける
        #     if blink_reset_num * 3 > next_fno - fno:
        #         continue

        #     # 前側の元に戻るキーフレ
        #     bf = VmdBoneFrame(fno + blink_reset_num, "両目")
        #     motion.bones["両目"].append(bf)
        #     output_motion.bones["両目"].append(bf.copy())

        #     # 後側の元に戻るキーフレ
        #     next_bf = VmdBoneFrame(next_fno - blink_reset_num, "両目")
        #     motion.bones["両目"].append(next_bf)
        #     output_motion.bones["両目"].append(next_bf.copy())

        #     logger.debug("まばたきクリア 始[{d}] 終[{r}]", d=bf.index, r=next_bf.index)


def fitted_x_function(x: float):
    y = (
        3.87509926e-08 * abs(x) ** 5
        - 9.78877468e-06 * abs(x) ** 4
        + 9.11972307e-04 * abs(x) ** 3
        - 3.94872605e-02 * abs(x) ** 2
        + 9.13973880e-01 * abs(x)
    )
    return y if x >= 0 else -y


def fitted_y_function(x: float):
    y = (
        1.47534033e-09 * abs(x) ** 5
        - 1.19583063e-06 * abs(x) ** 4
        + 2.32587413e-04 * abs(x) ** 3
        - 1.93864420e-02 * abs(x) ** 2
        + 8.94363417e-01 * abs(x)
    )
    return y if x >= 0 else -y


class BlinkCondition:
    def __init__(
        self,
        name: str,
        probability: float,
    ) -> None:
        """
        まばたきの条件
        name: 条件名(翻訳後を保持)
        ratio: デフォルト発生確率
        """
        self.name = __(name)
        self.probability = probability


class BlinkConditions(Enum):
    """まばたき条件リスト"""

    INTRO = BlinkCondition(name="イントロ", probability=100)
    ENDING = BlinkCondition(name="エンディング", probability=100)
    START_TURN = BlinkCondition(name="ターンの開始時", probability=100)
    AFTER_JUMP = BlinkCondition(name="キックやジャンプの着地後", probability=100)
    ARM_CROSS = BlinkCondition(name="腕が顔の前を横切った時", probability=80)
    LOOK_OVER = BlinkCondition(name="振り向いた時", probability=60)


BLINK_CONDITIONS: dict[str, float] = dict([(bs.value.name, bs.value.probability) for bs in BlinkConditions])
"""まばたき条件の名前と発生確率の辞書"""
