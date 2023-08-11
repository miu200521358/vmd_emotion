import os

from mlib.core.logger import MLogger
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_reader import VmdReader

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MotionMergeUsecase:
    def merge(
        self,
        motion_paths: list[str],
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

        output_motion = VmdMotion()
        output_motion.bones = motions[0].bones.copy()
        output_motion.morphs = motions[0].morphs.copy()

        all_merged_bone_names: set[str] = set([])
        all_merged_morph_names: set[str] = set([])
        for motion in motions[1:]:
            output_motion, frame_cnt, merged_bone_names, merged_morph_names = self.merge_motion(
                output_motion, motion, frame_cnt, total_frame_cnt
            )
            all_merged_bone_names |= merged_bone_names
            all_merged_morph_names |= merged_morph_names

        return output_motion

    def merge_motion(
        self,
        motion1: VmdMotion,
        motion2: VmdMotion,
        frame_cnt: int,
        total_frame_cnt: int,
    ) -> tuple[VmdMotion, int, set[str], set[str]]:
        merged_bone_names: set[str] = set(motion1.bones.names) | set(motion1.bones.names)
        merged_morph_names: set[str] = set(motion1.morphs.names) | set(motion1.morphs.names)
        output_motion = VmdMotion()

        for bone_name in merged_bone_names:
            for fno in sorted(set(motion1.bones[bone_name].indexes) | set(motion2.bones[bone_name].indexes)):
                logger.count("キーフレ統合", index=frame_cnt, total_index_count=total_frame_cnt, display_block=10000)

                # まずはキーフレがあるところを単純に足していく
                bf1 = motion1.bones[bone_name][fno]
                bf2 = motion2.bones[bone_name][fno]
                output_motion.append_bone_frame(bf1 + bf2)
                frame_cnt += 1

        return output_motion, frame_cnt, merged_bone_names, merged_morph_names
