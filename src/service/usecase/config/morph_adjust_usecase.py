import os

from mlib.core.interpolation import Interpolation, evaluate
from mlib.core.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MorphAdjustUsecase:
    def adjust(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        conditions: list[dict[str, str]],
    ) -> list[int]:
        """モーフ条件調整"""
        fnos: set[int] = set([])

        for condition in conditions:
            fnos |= self.adjust_condition(model, motion, output_motion, condition)

        return sorted(fnos)

    def adjust_condition(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        condition: dict[str, str],
    ) -> set[int]:
        morph_name = condition["morph_name"]
        min_ratio = float(condition["min"])
        max_ratio = float(condition["max"])
        min_v = 0
        max_v = int(max_ratio * 100) + int(abs(min_ratio) * 100)
        start_x = int(condition["start_x"])
        start_y = int(condition["start_y"])
        end_x = int(condition["end_x"])
        end_y = int(condition["end_y"])

        interpolation = Interpolation()
        interpolation.start.x = start_x
        interpolation.start.y = start_y
        interpolation.end.x = end_x
        interpolation.end.y = end_y

        logger.info("モーフ条件調整[{m}]", m=morph_name, decoration=MLogger.Decoration.LINE)

        for n, mf in enumerate(motion.morphs[morph_name]):
            logger.count("モーフ条件調整[{m}]", m=morph_name, index=n, total_index_count=len(motion.morphs[morph_name]), display_block=10000)
            _, ry, _ = evaluate(interpolation, min_v, int((mf.ratio + abs(min_ratio)) * 100), max_v)
            ratio = mf.ratio * ry

            new_mf = VmdMorphFrame(mf.index, mf.name, ratio)
            output_motion.append_morph_frame(new_mf)

        return set(motion.morphs[morph_name].indexes)
