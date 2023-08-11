import os

from mlib.core.logger import MLogger
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_reader import VmdReader

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MotionMergeUsecase:
    def merge(
        self,
        output_motion: VmdMotion,
        motion_paths: list[str],
    ) -> VmdMotion:
        """モーション統合"""

        logger.info("モーション全打ち統合", decoration=MLogger.Decoration.LINE)
        motions: list[VmdMotion] = []

        total_frame_cnt = 0
        frame_cnt = 0
        for motion_path in motion_paths:
            motion = VmdReader().read_by_filepath(motion_path)
            motions.append(motion)
            total_frame_cnt += sum([max(bfs.indexes) + 1 for bfs in motion.bones] + [max(mfs.indexes) + 1 for mfs in motion.morphs])

        output_motion.bones = motions[0].bones.copy()
        output_motion.morphs = motions[0].morphs.copy()

        all_merged_bone_names: set[str] = set([])
        all_merged_morph_names: set[str] = set([])
        for motion in motions[1:]:
            frame_cnt, merged_bone_names, merged_morph_names = self.merge_motion(output_motion, motion, frame_cnt, total_frame_cnt)
            all_merged_bone_names |= merged_bone_names
            all_merged_morph_names |= merged_morph_names

        logger.info("モーション不要キー削除", decoration=MLogger.Decoration.LINE)

        return output_motion

    def merge_motion(
        self, output_motion: VmdMotion, motion: VmdMotion, frame_cnt: int, total_frame_cnt: int
    ) -> tuple[int, set[str], set[str]]:
        merged_bone_names: list[str] = []
        merged_morph_names: list[str] = []

        for bfs in motion.bones:
            merged_bone_names.append(bfs.name)
            for fno in range(max(bfs.indexes) + 1):
                logger.count("キーフレ統合", index=frame_cnt, total_index_count=total_frame_cnt, display_block=10000)

                bf = motion.bones[bfs.name][fno]
                output_bf = output_motion.bones[bfs.name][fno]
                output_bf.position += bf.position
                output_bf.rotation *= bf.rotation
                output_motion.append_bone_frame(output_bf)
                frame_cnt += 1

        for mfs in motion.morphs:
            merged_morph_names.append(mfs.name)
            for fno in range(max(mfs.indexes) + 1):
                logger.count("キーフレ統合", index=frame_cnt, total_index_count=total_frame_cnt, display_block=10000)

                mf = motion.morphs[mfs.name][fno]
                output_mf = output_motion.morphs[mfs.name][fno]
                output_mf.ratio += mf.ratio
                output_motion.append_morph_frame(output_mf)
                frame_cnt += 1

        return frame_cnt, set(merged_bone_names), set(merged_morph_names)
