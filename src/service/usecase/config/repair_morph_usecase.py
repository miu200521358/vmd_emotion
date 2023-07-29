import os

import numpy as np

from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import BoneMorphOffset, GroupMorphOffset, MorphType, VertexMorphOffset
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class RepairMorphUsecase:
    def repair_morph(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        check_threshold: float,
        repair_factor: float,
    ) -> None:
        """モーフ破綻軽減"""
        # モーフによる変形があるキーフレ
        morph_fnos = sorted(set([mf.index for morph_name in motion.morphs.names for mf in motion.morphs[morph_name]]))

        if not morph_fnos:
            logger.warning("モーフによる変形があるキーフレが見つからなかったため、処理を中断します", decoration=MLogger.Decoration.BOX)
            return

        model.update_vertices_by_bone()

        logger.info("チェック対象モーフ抽出", decoration=MLogger.Decoration.LINE)

        # グループモーフの場合、中身が頂点モーフかボーンモーフであるかのチェック
        group_morphs: list[str] = []
        for morph in model.morphs:
            if morph.morph_type != MorphType.GROUP:
                continue
            for offset in morph.offsets:
                group_offset: GroupMorphOffset = offset
                if model.morphs[group_offset.morph_index].morph_type in [MorphType.VERTEX, MorphType.BONE]:
                    group_morphs.append(morph.name)
                    break

        # モーションの中から破綻をチェックする対象となるモーフ名リストを生成
        target_morph_names: list[str] = []
        for mfs in motion.morphs:
            if 0 == max(mfs.indexes):
                # 最大キーフレが0の場合、初期登録だけと見なしてスルー
                continue
            if mfs.name not in model.morphs:
                # そもそもモデルにないモーフであればスルー
                continue
            morph = model.morphs[mfs.name]
            if morph.morph_type in [MorphType.VERTEX, MorphType.BONE]:
                # 頂点モーフ・ボーンモーフだけチェック対象
                target_morph_names.append(mfs.name)
                continue
            if morph.name in group_morphs:
                # グループモーフで頂点・ボーンを含む場合、チェック対象
                target_morph_names.append(mfs.name)
                continue

        logger.info("モーフ最大変動量チェック", decoration=MLogger.Decoration.LINE)

        # モーフの変形量1.0の時の変形を保持
        morph_max_vertices: np.ndarray = np.zeros((len(target_morph_names), len(model.vertices), 3))

        for midx, morph_name in enumerate(target_morph_names):
            morph_max_vertices[midx] = self.get_vertex_positions(model, morph_name, 1.0)

        max_morph_vertex_positions = np.max(morph_max_vertices, axis=0)
        min_morph_vertex_positions = np.min(morph_max_vertices, axis=0)

        logger.info("モーフ破綻チェック", decoration=MLogger.Decoration.LINE)

        for fidx, fno in enumerate(morph_fnos):
            logger.count("モーフ破綻チェック", index=fidx, total_index_count=len(morph_fnos), display_block=100)

            fno_morph_ratios: dict[str, float] = {}
            fno_morph_reads: dict[str, bool] = {}

            for morph_name in target_morph_names:
                morph = model.morphs[morph_name]
                if morph.morph_type in [MorphType.VERTEX, MorphType.BONE, MorphType.GROUP]:
                    mf = motion.morphs[morph_name][fno]
                    fno_morph_ratios[morph_name] = mf.ratio
                    fno_morph_reads[morph_name] = mf.read

            if check_threshold > sum(list(fno_morph_ratios.values())):
                continue

            for _ in range(20):
                morph_vertices: np.ndarray = np.zeros((len(target_morph_names), len(model.vertices), 3))

                for midx, (morph_name, ratio) in enumerate(fno_morph_ratios.items()):
                    if np.isclose(ratio, 0.0):
                        continue
                    morph = model.morphs[morph_name]
                    morph_vertices[midx] = self.get_vertex_positions(model, morph_name, ratio)

                max_broken_vertices = np.where(np.sum(morph_vertices, axis=0) > max_morph_vertex_positions * repair_factor)
                min_broken_vertices = np.where(np.sum(morph_vertices, axis=0) < min_morph_vertex_positions * repair_factor)
                broken_vertex_indexes = np.unique(np.hstack((min_broken_vertices[0], max_broken_vertices[0])))

                if (
                    len(min_broken_vertices[0]) + len(max_broken_vertices[0])
                    < len(np.unique(np.where(np.sum(morph_vertices, axis=0) != 0.0)[0])) * 0.1
                ):
                    # 破綻頂点が見つからなかった場合、終了
                    break

                # 最大・最小を超える頂点が一定数ある場合、破綻している可能性があるとみなす
                key_morph_fnos: dict[str, int] = {}
                key_morph_ratios: dict[str, float] = {}
                key_morph_broken_vertices: dict[str, np.ndarray] = {}
                for midx, (morph_name, ratio) in enumerate(fno_morph_ratios.items()):
                    if np.isclose(ratio, 0.0):
                        continue
                    morph_start_fno, _, morph_end_fno = motion.morphs[morph_name].range_indexes(fno)
                    # 絶対値で大きい方の変化量を採用する
                    abs_ratios = [
                        np.abs(motion.morphs[morph_name][morph_start_fno].ratio),
                        np.abs(motion.morphs[morph_name][morph_end_fno].ratio),
                    ]
                    morph_ratio = np.max(abs_ratios)
                    morph_flg = np.argmax(abs_ratios)
                    key_morph_fnos[morph_name] = morph_start_fno if morph_flg == 0 else morph_end_fno
                    key_morph_ratios[morph_name] = morph_ratio
                    key_morph_broken_vertices[morph_name] = np.unique(np.where(morph_vertices[midx, broken_vertex_indexes] != 0.0)[0])

                # 破綻頂点があるモーフのうち、1番目に変化量が大きいモーフ名(ただしまばたきは除く)
                target_ratio_morph_names = [
                    m for m, r in key_morph_ratios.items() if not np.isclose(r, 0.0) and m not in IGNORE_MORPH_NAMES
                ]
                target_ratio_morph_ratios = [
                    r for m, r in key_morph_ratios.items() if not np.isclose(r, 0.0) and m not in IGNORE_MORPH_NAMES
                ]
                max_ratio_morph_name = target_ratio_morph_names[np.argmax(np.abs(target_ratio_morph_ratios))]
                target_fno = key_morph_fnos[max_ratio_morph_name]
                target_morph_original_ratio = motion.morphs[max_ratio_morph_name][target_fno].ratio
                motion.morphs[max_ratio_morph_name][target_fno].ratio *= 0.9
                # 出力は補正値のみ設定
                output_motion.morphs[max_ratio_morph_name].append(
                    VmdMorphFrame(target_fno, max_ratio_morph_name, target_morph_original_ratio * 0.9)
                )

                logger.info(
                    "モーフ破綻補正[{f}][{m}][{m1}:{f1} ({r1:.3f} -> {r2:.3f})]",
                    f=fno,
                    m=", ".join([f"{m}({r:.3f})" for m, r in fno_morph_ratios.items() if not np.isclose(r, 0.0)]),
                    m1=max_ratio_morph_name,
                    f1=key_morph_fnos[max_ratio_morph_name],
                    r1=target_morph_original_ratio,
                    r2=motion.morphs[max_ratio_morph_name][key_morph_fnos[max_ratio_morph_name]].ratio,
                )

                # 再チェックのため、取り直す
                fno_morph_ratios = {}
                fno_morph_reads = {}

                for morph_name in target_morph_names:
                    morph = model.morphs[morph_name]
                    if morph.morph_type in [MorphType.VERTEX, MorphType.BONE, MorphType.GROUP]:
                        mf = motion.morphs[morph_name][fno]
                        fno_morph_ratios[morph_name] = mf.ratio
                        fno_morph_reads[morph_name] = mf.read

    def get_vertex_positions(self, model: PmxModel, morph_name: str, ratio: float) -> np.ndarray:
        morph = model.morphs[morph_name]
        morph_vertices: np.ndarray = np.zeros((len(model.vertices), 3))

        if morph.morph_type == MorphType.VERTEX:
            for offset in morph.offsets:
                vertex_offset: VertexMorphOffset = offset
                morph_vertices[vertex_offset.vertex_index] += (vertex_offset.position * ratio).vector

        elif morph.morph_type == MorphType.BONE:
            motion = VmdMotion()
            motion.morphs[morph.name].append(VmdMorphFrame(0, morph.name, ratio))
            morph_matrixes = motion.animate_bone([0], model)

            for offset in morph.offsets:
                bone_offset: BoneMorphOffset = offset
                bone_vertices = model.vertices_by_bones.get(bone_offset.bone_index, [])
                for bone_vertex_index in bone_vertices:
                    vertex = model.vertices[bone_vertex_index]
                    mat = np.zeros((4, 4))
                    for bone_index, bone_weight in zip(vertex.deform.indexes, vertex.deform.weights):
                        mat += morph_matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
                    # 変形後の頂点位置の差分を保持
                    morph_vertices[bone_vertex_index] += (MMatrix4x4(mat) * MVector3D()).vector

        elif morph.morph_type == MorphType.GROUP:
            for offset in morph.offsets:
                part_offset: GroupMorphOffset = offset
                part_morph = model.morphs[part_offset.morph_index]
                if part_morph.morph_type == MorphType.VERTEX:
                    for vertex_offset in part_morph.offsets:
                        if vertex_offset.vertex_index not in morph_vertices:
                            morph_vertices[vertex_offset.vertex_index] = np.zeros(3)
                        morph_vertices[vertex_offset.vertex_index] += vertex_offset.position.vector

                elif part_morph.morph_type == MorphType.BONE:
                    motion = VmdMotion()
                    motion.morphs[part_morph.name].append(VmdMorphFrame(0, part_morph.name, ratio))
                    morph_matrixes = motion.animate_bone([0], model)

                    for bone_offset in part_morph.offsets:
                        bone_vertices = model.vertices_by_bones.get(bone_offset.bone_index, [])
                        for bone_vertex_index in bone_vertices:
                            vertex = model.vertices[bone_vertex_index]
                            mat = np.zeros((4, 4))
                            for bone_index, bone_weight in zip(vertex.deform.indexes, vertex.deform.weights):
                                mat += morph_matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
                            # 変形後の頂点位置の差分を保持
                            morph_vertices[bone_vertex_index] += (MMatrix4x4(mat) * MVector3D()).vector

        return morph_vertices


# 調整対象外モーフ
IGNORE_MORPH_NAMES = [
    "まばたき",
    "笑い",
    "ウインク",
    "右ウインク",
    "左ウインク",
    "ウィンク",
    "右ウィンク",
    "左ウィンク",
    "ｳｨﾝｸ",
    "右ｳｨﾝｸ",
    "左ｳｨﾝｸ",
    "ｳｲﾝｸ",
    "右ｳｲﾝｸ",
    "左ｳｲﾝｸ",
]
