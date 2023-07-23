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
                continue

            # 目線の向き
            gaze_dot = gaze_vector.dot(prev_gaze)
            logger.debug(f"fno[{fno:04d}], eye[{eye_global_direction_vector}], gaze[{gaze_vector}], dot[{gaze_dot:.3f}]")

            gaze_dots.append(gaze_dot)
            gaze_vectors.append(gaze_vector)
            prev_gaze = gaze_vector

        logger.info("目線変曲点抽出", decoration=MLogger.Decoration.LINE)
        # logger.debug(gaze_dots)

        infection_eyes = get_infections(gaze_dots, gaze_infection)
        # logger.debug(infection_eyes)

        logger.info("目線生成", decoration=MLogger.Decoration.LINE)

        bf = VmdBoneFrame(eye_fnos[0], "両目")
        motion.bones["両目"].append(bf)

        for fidx in infection_eyes:
            if 1 > fidx:
                continue

            fno = eye_fnos[fidx - 1]
            gaze_vector = gaze_vectors[fidx - 1]
            infection_gaze_vector = gaze_vectors[fidx]

            # 目線の変動が一定以上であれば目線を動かす
            gaze_full_qq = MQuaternion.rotate(gaze_vector, infection_gaze_vector)
            gaze_x_qq, gaze_y_qq, gaze_z_qq, _ = gaze_full_qq.separate_by_axis(MVector3D(1, 0, 0))

            gaze_ratio_x_qq = MQuaternion.slerp(MQuaternion(), gaze_x_qq, gaze_ratio_x)
            gaze_ratio_y_qq = MQuaternion.slerp(MQuaternion(), gaze_y_qq, gaze_ratio_y)
            gaze_ratio_qq = gaze_ratio_x_qq * gaze_ratio_y_qq

            bf = VmdBoneFrame(fno, "両目")
            bf.rotation = gaze_ratio_qq
            motion.bones["両目"].append(bf)
            output_motion.bones["両目"].append(bf.copy())

            logger.info("目線生成[{f}] 向き[{d}] 回転[{r}]", f=fno, d=infection_gaze_vector, r=gaze_ratio_qq.to_euler_degrees_mmd())
