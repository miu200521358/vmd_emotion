import os

from numpy.linalg import solve

from mlib.core.interpolation import IP_MAX, create_interpolation, get_infections
from mlib.core.logger import MLogger
from mlib.core.math import MQuaternion, MVector2D, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdBoneFrame, VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text

X_AXIS = MVector3D(1, 0, 0)
Z_AXIS = MVector3D(0, 0, -1)


class GazeUsecase:
    def create_gaze(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion_path: str,
        gaze_infection: float,
        gaze_ratio_x: float,
        gaze_limit_upper_x: int,
        gaze_limit_lower_x: int,
        gaze_ratio_y: float,
        gaze_limit_upper_y: int,
        gaze_limit_lower_y: int,
        gaze_reset_num: int,
        gaze_blink_ratio: float,
    ) -> tuple[VmdMotion, list[int]]:
        """目線生成"""

        # 既存は削除
        del motion.bones["両目"]
        del motion.morphs["まばたき"]

        output_motion = VmdMotion(output_motion_path)

        # 目線が動く可能性があるキーフレ一覧
        eye_fnos = sorted(set([bf.index for bone_name in model.bone_trees["両目"].names for bf in motion.bones[bone_name]]))

        logger.info("目線変動量取得", decoration=MLogger.Decoration.LINE)
        eye_matrixes = motion.animate_bone(eye_fnos, model, ["両目"], out_fno_log=True)

        gaze_fnos: set[int] = {0}
        gaze_fidxs: set[int] = {0}

        prev_gaze = None
        gaze_vectors: list[MVector3D] = []
        gaze_dots: list[float] = []
        for fidx, fno in enumerate(eye_fnos):
            logger.count("目線変動量取得", index=fidx, total_index_count=len(eye_fnos), display_block=100)
            eye_global_direction_vector = eye_matrixes[fno, "両目"].global_matrix * Z_AXIS
            gaze_vector = (eye_global_direction_vector - eye_matrixes[fno, "両目"].position).normalized()

            if not prev_gaze:
                # 初回はスルー
                prev_gaze = gaze_vector
                gaze_dots.append(1.0)
                continue

            # 目線の向き
            gaze_dot = gaze_vector.dot(prev_gaze)
            # logger.debug(f"fno[{fno:04d}], eye[{eye_global_direction_vector}], gaze[{gaze_vector}], dot[{gaze_dot:.3f}]")

            gaze_dots.append(gaze_dot)
            gaze_vectors.append(gaze_vector)
            prev_gaze = gaze_vector

        logger.info("目線変曲点抽出", decoration=MLogger.Decoration.LINE)
        # logger.debug(gaze_dots)

        infection_eyes = get_infections(gaze_dots, (1 - gaze_infection) * 0.02)
        # logger.debug(infection_eyes)

        logger.info("目線生成", decoration=MLogger.Decoration.LINE)

        # 最初は静止
        start_bf = VmdBoneFrame(eye_fnos[0], "両目")
        motion.append_bone_frame(start_bf)
        output_motion.append_bone_frame(start_bf.copy())

        # 最後は静止
        end_bf = VmdBoneFrame(eye_fnos[-1], "両目")
        motion.append_bone_frame(end_bf)
        output_motion.append_bone_frame(end_bf.copy())

        for i, iidx in enumerate(infection_eyes):
            logger.count("目線生成", index=i, total_index_count=len(infection_eyes), display_block=1000)

            if 1 > i:
                continue

            fno = eye_fnos[iidx - 1]

            if 1 < i:
                prev_fno = eye_fnos[iidx - 2]
                if 5 > fno - prev_fno:
                    # 前の目線からあまりにも近い場合スルー
                    continue

            gaze_vector = gaze_vectors[iidx - 1]
            infection_gaze_vector = gaze_vectors[iidx]

            # 目線の変動が一定以上であれば目線を動かす
            gaze_full_qq = MQuaternion.rotate(gaze_vector, infection_gaze_vector)
            # Zは前向きの捩れになるので捨てる
            gaze_original_x_qq, gaze_original_y_qq, _, _ = gaze_full_qq.separate_by_axis(X_AXIS)

            # 目線の上下運動
            x = gaze_original_x_qq.to_signed_degrees(Z_AXIS)
            # 補正値を求める(初期で少し下げ目にしておく)
            correct_x = fitted_x_function(x) * gaze_ratio_x - 2
            gaze_x_qq = MQuaternion.from_axis_angles(gaze_original_x_qq.xyz, correct_x)

            # 目線の左右運動
            y = gaze_original_y_qq.to_signed_degrees(Z_AXIS)
            # 補正値を求める
            correct_y = fitted_y_function(y) * gaze_ratio_y
            gaze_y_qq = MQuaternion.from_axis_angles(gaze_original_y_qq.xyz, correct_y)

            gaze_qq = gaze_x_qq * gaze_y_qq
            gaze_degrees = gaze_qq.to_euler_degrees()
            # Z回転を殺して上下限を設定する
            gaze_x_degree = max(gaze_limit_lower_x, min(gaze_limit_upper_x, gaze_degrees.x))
            gaze_y_degree = max(gaze_limit_lower_y, min(gaze_limit_upper_y, gaze_degrees.y))
            gaze_xy_qq = MQuaternion.from_euler_degrees(gaze_x_degree, gaze_y_degree, 0)

            bf = VmdBoneFrame(fno, "両目")
            bf.rotation = gaze_xy_qq
            motion.append_bone_frame(bf)
            output_motion.append_bone_frame(bf.copy())
            gaze_fnos |= {fno}
            gaze_fidxs |= {iidx - 1}

            if 0 > gaze_x_degree:
                # 目線が下を向いていたらまぶたも少し下げる
                gaze_x_ratio = (gaze_x_degree / gaze_limit_lower_x) * gaze_blink_ratio
            else:
                # 目線が上を向いていたらまぶたを少し上げる
                gaze_x_ratio = (gaze_x_degree / gaze_limit_upper_x) * -gaze_blink_ratio

            mf = VmdMorphFrame(fno, "まばたき")
            mf.ratio = gaze_x_ratio
            motion.append_morph_frame(mf)
            output_motion.append_morph_frame(mf.copy())

            logger.debug("目線生成[{f}] 向き[{d}] 回転[{r}]", f=fno, d=infection_gaze_vector, r=gaze_qq.to_euler_degrees_mmd())

        for i, (iidx, fno) in enumerate(zip(gaze_fidxs, gaze_fnos)):
            logger.count("目線クリア", index=i, total_index_count=len(infection_eyes), display_block=100)

            # 前側の元に戻るキーフレ
            if gaze_reset_num < fno - gaze_reset_num and not [f for f in range(-gaze_reset_num - 1, 0) if (fno - f) in gaze_fnos]:
                before_reset_fno = int(fno - gaze_reset_num / 2)
                bf = VmdBoneFrame(before_reset_fno, "両目")
                motion.append_bone_frame(bf)
                output_motion.append_bone_frame(bf.copy())

                mf = VmdMorphFrame(before_reset_fno, "まばたき")
                motion.append_morph_frame(mf)
                output_motion.append_morph_frame(mf.copy())

                logger.debug("目線クリア 始[{d}]", d=before_reset_fno)

            # 後側の元に戻るキーフレ
            if not [f for f in range(1, gaze_reset_num + 1) if (fno + f) in gaze_fnos]:
                after_reset_fno = int(fno + gaze_reset_num / 2)
                next_bf = VmdBoneFrame(after_reset_fno, "両目")
                motion.append_bone_frame(next_bf)
                output_motion.append_bone_frame(next_bf.copy())

                mf = VmdMorphFrame(after_reset_fno, "まばたき")
                motion.append_morph_frame(mf)
                output_motion.append_morph_frame(mf.copy())

                logger.debug("目線クリア 終[{r}]", r=after_reset_fno)

        eye_fnos = output_motion.bones["両目"].indexes
        for fidx, (prev_fno, now_fno, next_fno) in enumerate(zip(eye_fnos[:-2:2], eye_fnos[1:-1:2], eye_fnos[2::2])):
            logger.count("目線補間曲線", index=fidx, total_index_count=len(eye_fnos), display_block=100)

            prev_bf = output_motion.bones["両目"][prev_fno]
            now_bf = output_motion.bones["両目"][now_fno]
            next_bf = output_motion.bones["両目"][next_fno]

            prev_degree = prev_bf.rotation.to_signed_degrees(Z_AXIS)
            now_degree = now_bf.rotation.to_signed_degrees(Z_AXIS)
            next_degree = next_bf.rotation.to_signed_degrees(Z_AXIS)

            prev_degree = 1
            now_degree = now_bf.rotation.dot(prev_bf.rotation)
            next_degree = next_bf.rotation.dot(now_bf.rotation)

            x1 = 0
            x2 = now_fno - prev_fno
            x3 = next_fno - prev_fno

            a, b, c = solve([[x1**2, x1, 1], [x2**2, x2, 1], [x3**2, x3, 1]], [prev_degree, now_degree, next_degree])

            now_degrees: list[float] = []
            for fidx in range(int(now_fno - prev_fno)):
                now_degrees.append(a * fidx**2 + b * fidx + c)
            now_interpolation = create_interpolation(now_degrees)

            next_degrees: list[float] = []
            for fidx in range(int(now_fno - prev_fno), int(next_fno - prev_fno)):
                next_degrees.append(a * fidx**2 + b * fidx + c)
            next_interpolation = create_interpolation(next_degrees)

            prev_bf.interpolations.rotation.end = MVector2D(IP_MAX, IP_MAX) - now_interpolation.start
            now_bf.interpolations.rotation.start = now_interpolation.start
            now_bf.interpolations.rotation.end = MVector2D(IP_MAX, IP_MAX) - next_interpolation.start
            next_bf.interpolations.rotation.start = next_interpolation.start
            next_bf.interpolations.rotation.end = next_interpolation.end

            logger.debug(
                f"目線補間曲線 係数[{a:.3f}, {b:.3f}, {c:.3f}] prev[{prev_bf.index}][{prev_bf.interpolations.rotation}] "
                + f"now[{now_bf.index}][{now_bf.interpolations.rotation}]"
            )

        return output_motion, sorted(gaze_fnos)


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
