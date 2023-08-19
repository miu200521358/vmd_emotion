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
        output_motion_path: str,
        conditions: list[dict[str, str]],
    ) -> tuple[VmdMotion, list[int]]:
        """モーフ条件調整"""
        fnos: set[int] = set([])

        output_motion = motion.copy()
        output_motion.path = output_motion_path

        for condition in conditions:
            fnos |= self.adjust_condition(model, motion, output_motion, condition)

        return output_motion, sorted(fnos)

    def adjust_condition(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        condition: dict[str, str],
    ) -> set[int]:
        morph_name = condition["morph_name"]
        replace_morph_name = condition["replace_morph_name"]
        ratio = float(condition["ratio"])
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
            r = mf.ratio * ry * ratio

            mname = replace_morph_name if replace_morph_name else mf.name
            prev_index, now_index, next_index = output_motion.morphs[mname].range_indexes(mf.index)
            new_mf = VmdMorphFrame(now_index, mname, r)

            if prev_index == now_index == next_index:
                # 今のキーに既にキーフレがある場合
                if replace_morph_name:
                    # 置き換えの場合、加算
                    now_mf = output_motion.morphs[mname][now_index]
                    output_motion.append_morph_frame(now_mf + new_mf)
                else:
                    # 置き換えしない場合、そのまま置換
                    output_motion.append_morph_frame(new_mf)
            else:
                # 該当キーにキーフレがない場合、置換
                output_motion.append_morph_frame(new_mf)

        if replace_morph_name:
            del output_motion.morphs[morph_name]

        return set(motion.morphs[morph_name].indexes)
