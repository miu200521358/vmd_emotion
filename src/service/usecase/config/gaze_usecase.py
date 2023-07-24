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


class GazeUsecase:
    def create_gaze(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        gaze_infection: float,
        gaze_ratio_x: float,
        gaze_ratio_y: float,
        gaze_reset_num: int,
    ) -> None:
        """目線生成"""

        if "両目" in motion.bones.names:
            # 既存の両目キーフレは削除
            del motion.bones["両目"]

        # 目線が動く可能性があるキーフレ一覧
        eye_fnos = sorted(set([bf.index for bone_name in model.bone_trees["両目"].names for bf in motion.bones[bone_name]]))

        logger.info("目線変動量取得", decoration=MLogger.Decoration.LINE)
        eye_matrixes = motion.animate_bone(eye_fnos, model, ["両目"], out_fno_log=True)

        prev_gaze = None
        gaze_vectors: list[MVector3D] = []
        gaze_dots: list[float] = []
        for fidx, fno in enumerate(eye_fnos):
            logger.count("目線変動量取得", index=fidx, total_index_count=len(eye_fnos), display_block=100)
            eye_global_direction_vector = eye_matrixes[fno, "両目"].global_matrix * MVector3D(0, 0, -1)
            gaze_vector = (eye_global_direction_vector - eye_matrixes[fno, "両目"].position).normalized()

            if not prev_gaze:
                # 初回はスルー
                prev_gaze = gaze_vector
                gaze_dots.append(1.0)
                continue

            # 目線の向き
            gaze_dot = gaze_vector.dot(prev_gaze)
            logger.debug(f"fno[{fno:04d}], eye[{eye_global_direction_vector}], gaze[{gaze_vector}], dot[{gaze_dot:.3f}]")

            gaze_dots.append(gaze_dot)
            gaze_vectors.append(gaze_vector)
            prev_gaze = gaze_vector

        logger.info("目線変曲点抽出", decoration=MLogger.Decoration.LINE)
        # logger.debug(gaze_dots)

        infection_eyes = get_infections(gaze_dots, gaze_infection * 0.1)
        # logger.debug(infection_eyes)

        logger.info("目線生成", decoration=MLogger.Decoration.LINE)

        # 最初は静止
        start_bf = VmdBoneFrame(eye_fnos[0], "両目")
        motion.bones["両目"].append(start_bf)
        output_motion.bones["両目"].append(start_bf.copy())

        # 最後は静止
        end_bf = VmdBoneFrame(eye_fnos[-1], "両目")
        motion.bones["両目"].append(end_bf)
        output_motion.bones["両目"].append(end_bf.copy())

        for i, iidx in enumerate(infection_eyes):
            logger.count("目線生成", index=i, total_index_count=len(infection_eyes), display_block=1000)

            if 1 > i:
                continue

            fno = eye_fnos[iidx - 1]
            gaze_vector = gaze_vectors[iidx - 1]
            infection_gaze_vector = gaze_vectors[iidx]

            # 目線の変動が一定以上であれば目線を動かす
            gaze_full_qq = MQuaternion.rotate(gaze_vector, infection_gaze_vector)
            # Zは前向きの捩れになるので捨てる
            gaze_original_x_qq, gaze_original_y_qq, gaze_z_qq, _ = gaze_full_qq.separate_by_axis(MVector3D(1, 0, 0))

            # 目線の上下運動
            x = gaze_original_x_qq.to_signed_degrees(MVector3D(0, 0, -1))
            # 補正値を求める(初期で少し下げ目にしておく)
            correct_x = fitted_x_function(x) * gaze_ratio_x - 2
            gaze_x_qq = MQuaternion.from_axis_angles(gaze_original_x_qq.xyz, correct_x)

            # 目線の左右運動
            y = gaze_original_y_qq.to_signed_degrees(MVector3D(0, 0, -1))
            # 補正値を求める
            correct_y = fitted_y_function(y) * gaze_ratio_y
            gaze_y_qq = MQuaternion.from_axis_angles(gaze_original_y_qq.xyz, correct_y)

            gaze_qq = gaze_x_qq * gaze_y_qq

            bf = VmdBoneFrame(fno, "両目")
            bf.rotation = gaze_qq
            motion.bones["両目"].append(bf)
            output_motion.bones["両目"].append(bf.copy())

            logger.debug("目線生成[{f}] 向き[{d}] 回転[{r}]", f=fno, d=infection_gaze_vector, r=gaze_qq.to_euler_degrees_mmd())

        for i, (iidx, next_iidx) in enumerate(zip(infection_eyes[:-1], infection_eyes[1:])):
            logger.count("目線クリア", index=i, total_index_count=len(infection_eyes), display_block=100)

            fno = eye_fnos[iidx]
            next_fno = eye_fnos[next_iidx]

            # 前の目線との間に静止期間を設ける
            if gaze_reset_num * 3 > next_fno - fno:
                continue

            # 前側の元に戻るキーフレ
            bf = VmdBoneFrame(fno + gaze_reset_num, "両目")
            motion.bones["両目"].append(bf)
            output_motion.bones["両目"].append(bf.copy())

            # 後側の元に戻るキーフレ
            next_bf = VmdBoneFrame(next_fno - gaze_reset_num, "両目")
            motion.bones["両目"].append(next_bf)
            output_motion.bones["両目"].append(next_bf.copy())

            logger.debug("目線クリア 始[{d}] 終[{r}]", d=bf.index, r=next_bf.index)


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
