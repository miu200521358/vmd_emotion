import os

from mlib.core.interpolation import create_interpolation, get_infections

from mlib.core.logger import MLogger
from mlib.vmd.vmd_collection import VmdBoneNameFrames, VmdMorphNameFrames, VmdMotion
from mlib.vmd.vmd_part import VmdBoneFrame
from mlib.vmd.vmd_reader import VmdReader

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MotionMergeUsecase:
    def merge(
        self,
        motion_paths: list[str],
        output_motion_path: str,
    ) -> VmdMotion:
        """モーション統合"""

        logger.info("モーション統合", decoration=MLogger.Decoration.LINE)
        motions: list[VmdMotion] = []

        total_frame_cnt = 0
        frame_cnt = 0
        for motion_path in motion_paths:
            motion1 = VmdReader().read_by_filepath(motion_path)
            motions.append(motion1)
            total_frame_cnt += sum([max(bfs.indexes) + 1 for bfs in motion1.bones])
            total_frame_cnt += sum([max(mfs.indexes) + 1 for mfs in motion1.morphs])

        merge_motion = VmdMotion()
        merge_motion.bones = motions[0].bones.copy()
        merge_motion.morphs = motions[0].morphs.copy()

        for motion in motions[1:]:
            merge_motion, frame_cnt = self.merge_motion(merge_motion, motion, frame_cnt, total_frame_cnt)

        output_motion = VmdMotion(output_motion_path)

        # 統合しなかったボーンとモーフを追加する
        for motion in motions:
            for bone_name in motion.bones.names:
                if bone_name in merge_motion.bones.names:
                    output_motion.bones.append(merge_motion.bones[bone_name])
                else:
                    output_motion.bones.append(motion.bones[bone_name])

            for morph_name in motion.morphs.names:
                if morph_name in merge_motion.morphs.names:
                    output_motion.morphs.append(merge_motion.morphs[morph_name])
                else:
                    output_motion.morphs.append(motion.morphs[morph_name])

        return output_motion

    def merge_motion(
        self,
        motion1: VmdMotion,
        motion2: VmdMotion,
        frame_cnt: int,
        total_frame_cnt: int,
    ) -> tuple[VmdMotion, int]:
        """モーション同士の統合"""
        # 両方にキーがあるのだけ統合
        merged_bone_names: set[str] = set(motion2.bones.names)
        merged_morph_names: set[str] = set(motion2.morphs.names)
        output_motion = VmdMotion()

        for bone_name in merged_bone_names:
            for fno in sorted(set(motion1.bones[bone_name].indexes) | set(motion2.bones[bone_name].indexes)):
                logger.count("ボーンキーフレーム統合", index=frame_cnt, total_index_count=total_frame_cnt, display_block=10000)

                # まずはキーフレがあるところを単純に足していく
                bf1 = motion1.bones[bone_name][fno]
                bf2 = motion2.bones[bone_name][fno]
                output_motion.insert_bone_frame(bf1 + bf2)
                frame_cnt += 1

        self.ensure_bone_motion(output_motion, motion1, motion2)

        for morph_name in merged_morph_names:
            for fno in sorted(set(motion1.morphs[morph_name].indexes) | set(motion2.morphs[morph_name].indexes)):
                logger.count("モーフキーフレーム統合", index=frame_cnt, total_index_count=total_frame_cnt, display_block=10000)

                # まずはキーフレがあるところを単純に足していく
                mf1 = motion1.morphs[morph_name][fno]
                mf2 = motion2.morphs[morph_name][fno]
                output_motion.insert_morph_frame(mf1 + mf2)
                frame_cnt += 1

        self.ensure_morph_motion(output_motion, motion1, motion2)

        return output_motion, frame_cnt

    def ensure_bone_motion(self, output_motion: VmdMotion, motion1: VmdMotion, motion2: VmdMotion) -> None:
        """ボーンキーフレの検算"""

        for bone_name in output_motion.bones.names:
            for prev_fno, next_fno in zip(output_motion.bones[bone_name].indexes, output_motion.bones[bone_name].indexes[1:]):
                position_x_dots: list[float] = [0.0]
                position_y_dots: list[float] = [0.0]
                position_z_dots: list[float] = [0.0]
                rotation_dots: list[float] = [1.0]

                ensure_bfs = VmdBoneNameFrames()
                output_bfs = VmdBoneNameFrames()

                logger.debug(f"[{bone_name}][{prev_fno} - {next_fno}] ------------------------------")

                prev_ensure_bf: VmdBoneFrame = None
                for fno in range(prev_fno, next_fno + 1):
                    # 補間曲線を生成する
                    bf1 = motion1.bones[bone_name][fno]
                    bf2 = motion2.bones[bone_name][fno]

                    ensure_bf = bf1 + bf2
                    ensure_bfs.append(ensure_bf)

                    if prev_ensure_bf:
                        position_x_dots.append(ensure_bf.position.x - prev_ensure_bf.position.x)
                        position_y_dots.append(ensure_bf.position.y - prev_ensure_bf.position.y)
                        position_z_dots.append(ensure_bf.position.z - prev_ensure_bf.position.z)
                        rotation_dots.append(ensure_bf.rotation.dot(prev_ensure_bf.rotation))

                    prev_ensure_bf = ensure_bf

                output_motion.bones[bone_name].data[next_fno].interpolations.translation_x = create_interpolation(position_x_dots)
                output_motion.bones[bone_name].data[next_fno].interpolations.translation_y = create_interpolation(position_y_dots)
                output_motion.bones[bone_name].data[next_fno].interpolations.translation_z = create_interpolation(position_z_dots)
                output_motion.bones[bone_name].data[next_fno].interpolations.rotation = create_interpolation(rotation_dots)

                logger.debug(f"[{bone_name}] interpolations[{next_fno}]: {output_motion.bones[bone_name].data[next_fno].interpolations}")

                # -----------------------

                fnos: list[int] = []
                position_x_diff_dots: list[float] = [0.0]
                position_y_diff_dots: list[float] = [0.0]
                position_z_diff_dots: list[float] = [0.0]
                rotation_diff_dots: list[float] = [1.0]

                for fno in range(prev_fno, next_fno + 1):
                    # 合成した場合の値と、出力予定の値を1Fずつ保持
                    bf1 = motion1.bones[bone_name][fno]
                    bf2 = motion2.bones[bone_name][fno]

                    ensure_bf = bf1 + bf2
                    ensure_bfs.append(ensure_bf)

                    output_bf = output_motion.bones[bone_name][fno]
                    output_bfs.append(output_bf)

                    position_x_diff_dot = ensure_bf.position.x - output_bf.position.x
                    position_y_diff_dot = ensure_bf.position.y - output_bf.position.y
                    position_z_diff_dot = ensure_bf.position.z - output_bf.position.z
                    rotation_diff_dot = ensure_bf.rotation.dot(output_bf.rotation)

                    logger.debug(
                        f"[{bone_name}][{fno}], ensure_position[{ensure_bf.position}] output_position[{output_bf.position}] "
                        + f"position_x_diff_dot[{position_x_diff_dot:.5f}] position_y_diff_dot[{position_y_diff_dot:.5f}] "
                        + f"position_z_diff_dot[{position_z_diff_dot:.5f}], ensure_rotation[{ensure_bf.rotation.to_euler_degrees()}] "
                        + f"output_rotation[{output_bf.rotation.to_euler_degrees()}] rotation_dot[{rotation_diff_dot:.5f}]"
                    )

                    fnos.append(fno)
                    position_x_diff_dots.append(position_x_diff_dot)
                    position_y_diff_dots.append(position_y_diff_dot)
                    position_z_diff_dots.append(position_z_diff_dot)
                    rotation_diff_dots.append(rotation_diff_dot)

                # -----------------------

                infection_position_x_fidxs = get_infections(position_x_diff_dots, threshold=1e-5).tolist()
                infection_position_y_fidxs = get_infections(position_y_diff_dots, threshold=1e-5).tolist()
                infection_position_z_fidxs = get_infections(position_z_diff_dots, threshold=1e-5).tolist()
                infection_rotation_fidxs = get_infections(rotation_diff_dots, threshold=1e-5).tolist()

                for infection_fidx in sorted(
                    set(infection_position_x_fidxs + infection_position_y_fidxs + infection_position_z_fidxs + infection_rotation_fidxs)
                ):
                    infection_fno = fnos[infection_fidx]
                    logger.debug(f"[{bone_name}] infection_fno: {infection_fno}")

                    bf1 = motion1.bones[bone_name][infection_fno]
                    bf2 = motion2.bones[bone_name][infection_fno]

                    ensure_bf = bf1 + bf2
                    output_motion.insert_bone_frame(ensure_bf)

    def ensure_morph_motion(self, output_motion: VmdMotion, motion1: VmdMotion, motion2: VmdMotion) -> None:
        """モーフキーフレの検算"""

        for morph_name in output_motion.morphs.names:
            for prev_fno, next_fno in zip(output_motion.morphs[morph_name].indexes, output_motion.morphs[morph_name].indexes[1:]):
                ensure_morphs = VmdMorphNameFrames()
                output_morphs = VmdMorphNameFrames()

                logger.debug(f"[{morph_name}][{prev_fno} - {next_fno}] ------------------------------")

                # -----------------------

                fnos: list[int] = []
                ratio_diff_dots: list[float] = [0.0]

                for fno in range(prev_fno, next_fno + 1):
                    # 合成した場合の値と、出力予定の値を1Fずつ保持
                    morph1 = motion1.morphs[morph_name][fno]
                    morph2 = motion2.morphs[morph_name][fno]

                    ensure_morph = morph1 + morph2
                    ensure_morphs.append(ensure_morph)

                    output_morph = output_motion.morphs[morph_name][fno]
                    output_morphs.append(output_morph)

                    ratio_diff_dot = ensure_morph.ratio - output_morph.ratio

                    logger.debug(
                        f"[{morph_name}][{fno}], ensure_ratio[{ensure_morph.ratio:.3f}] "
                        + f"output_ratio[{output_morph.ratio:.3f}] ratio_dot[{ratio_diff_dot:.5f}]"
                    )

                    fnos.append(fno)
                    ratio_diff_dots.append(ratio_diff_dot)

                # -----------------------

                infection_ratio_fidxs = get_infections(ratio_diff_dots, threshold=1e-5).tolist()

                for infection_fidx in infection_ratio_fidxs:
                    infection_fno = fnos[infection_fidx]
                    logger.debug(f"[{morph_name}]infection_fno: {infection_fno}")

                    morph1 = motion1.morphs[morph_name][infection_fno]
                    morph2 = motion2.morphs[morph_name][infection_fno]

                    ensure_morph = morph1 + morph2
                    output_motion.insert_morph_frame(ensure_morph)
