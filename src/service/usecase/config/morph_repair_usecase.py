import os

import numpy as np

from mlib.core.logger import MLogger
from mlib.core.math import MMatrix4x4, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import BoneMorphOffset, GroupMorphOffset, MorphType, VertexMorphOffset
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class MorphRepairUsecase:
    def repair(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion_path: str,
        check_threshold: float,
        repair_factor: float,
    ) -> list[int]:
        """モーフ破綻軽減"""
        # モーフによる変形があるキーフレ
        morph_fnos = sorted(set([mf.index for morph_name in motion.morphs.names for mf in motion.morphs[morph_name]]))

        if not morph_fnos:
            logger.warning("モーフによる変形があるキーフレが見つからなかったため、処理を中断します", decoration=MLogger.Decoration.BOX)
            return []

        output_motion = VmdMotion(output_motion_path)
        repair_fnos: set[int] = {0}
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

        # モーフの変形量閾値の時の変形を保持
        morph_max_vertices: np.ndarray = np.zeros((len(target_morph_names), len(model.vertices), 3))
        morph_vertex_indexes: dict[str, set[int]] = {}

        for midx, morph_name in enumerate(target_morph_names):
            vertex_indexes, morph_max_vertices[midx] = self.get_vertex_positions(model, morph_name, repair_factor)
            morph_vertex_indexes[morph_name] = vertex_indexes

        max_morph_vertex_positions = np.max(np.abs(morph_max_vertices), axis=0)

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

            for i in range(100):
                key_morph_vertex_positions: np.ndarray = np.zeros((len(target_morph_names), len(model.vertices), 3))

                for midx, (morph_name, ratio) in enumerate(fno_morph_ratios.items()):
                    if np.isclose(ratio, 0.0):
                        continue
                    morph = model.morphs[morph_name]
                    _, key_morph_vertex_positions[midx] = self.get_vertex_positions(model, morph_name, ratio)

                broken_vertex_indexes = np.unique(
                    np.where(
                        np.logical_and(
                            np.sum(np.abs(key_morph_vertex_positions), axis=0) > max_morph_vertex_positions,
                            ~np.isclose(max_morph_vertex_positions, 0.0),
                        )
                    )[0]
                )

                if not len(broken_vertex_indexes):
                    break

                max_factor_morph_vertex_positions = max_morph_vertex_positions[broken_vertex_indexes]
                broken_factor_morph_vertex_positions = np.sum(key_morph_vertex_positions[:, broken_vertex_indexes], axis=0)
                factor_broken_vertex_indexes = np.unique(
                    np.where(
                        np.logical_and(
                            np.abs(broken_factor_morph_vertex_positions / max_factor_morph_vertex_positions) > repair_factor,
                            np.abs(broken_factor_morph_vertex_positions) > 0.05,
                        )
                    )[0]
                )

                logger.debug(
                    f"[{fno}({i})] broken[{np.round(np.sum(broken_factor_morph_vertex_positions, axis=0), decimals=3)}]"
                    + f" max[{np.round(np.sum(max_factor_morph_vertex_positions, axis=0), decimals=3)}]"
                    + f" indexes[{factor_broken_vertex_indexes}]"
                )

                if not len(factor_broken_vertex_indexes):
                    # 指定を超えた破綻頂点がなかった場合、終了
                    break

                # 最大・最小を超える頂点が一定数ある場合、破綻している可能性があるとみなす
                key_morph_fnos: dict[str, int] = {}
                key_morph_broken_vertex_index_counts: list[float] = []
                key_morph_broken_vertex_positions: list[float] = []

                for midx, (morph_name, ratio) in enumerate(fno_morph_ratios.items()):
                    if np.isclose(ratio, 0.0):
                        key_morph_broken_vertex_index_counts.append(0)
                        key_morph_broken_vertex_positions.append(0)
                        continue
                    morph_start_fno, _, morph_end_fno = motion.morphs[morph_name].range_indexes(fno)
                    # 絶対値で大きい方の変化量を採用する
                    abs_ratios = [
                        np.abs(motion.morphs[morph_name][morph_start_fno].ratio),
                        np.abs(motion.morphs[morph_name][morph_end_fno].ratio),
                    ]
                    morph_flg = np.argmax(abs_ratios)
                    # 破綻している場合の調整キーフレ
                    key_morph_fnos[morph_name] = morph_start_fno if morph_flg == 0 else morph_end_fno
                    # 破綻している頂点とモーフの変形対象頂点の重複INDEX
                    key_morph_broken_vertex_indexes = np.array(
                        list(morph_vertex_indexes[morph_name] & set(broken_vertex_indexes[factor_broken_vertex_indexes].tolist()))
                    )
                    key_morph_broken_vertex_index_counts.append(float(len(key_morph_broken_vertex_indexes)))
                    # 破綻している頂点がモーフの変形範囲である場合、変形量の合計を取得
                    if 0 < len(key_morph_broken_vertex_indexes):
                        key_morph_broken_vertex_positions.append(
                            float(np.sum(np.abs(key_morph_vertex_positions[midx, key_morph_broken_vertex_indexes])))
                        )
                    else:
                        key_morph_broken_vertex_positions.append(0)

                logger.debug(
                    f"[{fno}({i})] key_morph_broken_vertex_indexes[{key_morph_broken_vertex_index_counts}], "
                    + f"key_morph_broken_vertex_positions[{key_morph_broken_vertex_positions}]"
                )

                # 破綻頂点があるモーフのうち、破綻頂点INDEXと被ってるのが多いのが最優先（2番目は変動量）
                max_ratio_morph_name = list(fno_morph_ratios.keys())[
                    np.lexsort((key_morph_broken_vertex_positions, key_morph_broken_vertex_index_counts))[-1]
                ]
                target_fno = key_morph_fnos[max_ratio_morph_name]

                # 変化量を小さくする
                target_morph_original_ratio = motion.morphs[max_ratio_morph_name][target_fno].ratio
                target_morph_repair_ratio = target_morph_original_ratio - (
                    max(0.05, abs(target_morph_original_ratio) * 0.1) * np.sign(target_morph_original_ratio)
                )
                motion.morphs[max_ratio_morph_name][target_fno].ratio = target_morph_repair_ratio
                # 出力は補正値のみ設定
                rmf = VmdMorphFrame(target_fno, max_ratio_morph_name, target_morph_repair_ratio)
                output_motion.append_morph_frame(rmf)
                repair_fnos |= {target_fno}

                logger.info(
                    "モーフ破綻補正[{f}({i})][{m}][{m1}:{f1} ({r1:.3f} -> {r2:.3f})]",
                    f=fno,
                    i=i,
                    m=", ".join([f"{m}({r:.3f})" for m, r in fno_morph_ratios.items() if not np.isclose(r, 0.0)]),
                    m1=max_ratio_morph_name,
                    f1=key_morph_fnos[max_ratio_morph_name],
                    r1=target_morph_original_ratio,
                    r2=target_morph_repair_ratio,
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

        return sorted(repair_fnos)

    def get_vertex_positions(self, model: PmxModel, morph_name: str, ratio: float) -> tuple[set[int], np.ndarray]:
        morph = model.morphs[morph_name]
        morph_vertices: np.ndarray = np.zeros((len(model.vertices), 3))
        vertex_indexes: set[int] = set([])

        if morph.morph_type == MorphType.VERTEX:
            for offset in morph.offsets:
                vertex_offset: VertexMorphOffset = offset
                morph_vertices[vertex_offset.vertex_index] += (vertex_offset.position * ratio).vector
                vertex_indexes |= {vertex_offset.vertex_index}

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
                    vertex_indexes |= {bone_vertex_index}

        elif morph.morph_type == MorphType.GROUP:
            for offset in morph.offsets:
                part_offset: GroupMorphOffset = offset
                part_morph = model.morphs[part_offset.morph_index]
                if part_morph.morph_type == MorphType.VERTEX:
                    for vertex_offset in part_morph.offsets:
                        if vertex_offset.vertex_index not in morph_vertices:
                            morph_vertices[vertex_offset.vertex_index] = np.zeros(3)
                        morph_vertices[vertex_offset.vertex_index] += vertex_offset.position.vector
                        vertex_indexes |= {vertex_offset.vertex_index}

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
                            vertex_indexes |= {bone_vertex_index}

        return vertex_indexes, morph_vertices
