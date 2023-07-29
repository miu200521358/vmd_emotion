import os
from itertools import product

import numpy as np

from mlib.base.exception import MApplicationException
from mlib.base.logger import MLogger
from mlib.base.math import MMatrix4x4, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.pmx.pmx_part import BoneMorphOffset, MorphType, VertexMorphOffset
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdMorphFrame
from mlib.vmd.vmd_tree import VmdBoneFrameTrees
from service.usecase.config.blink_usecase import BLINK_CONDITIONS

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text


class LoadUsecase:
    def valid_model(self, model: PmxModel) -> None:
        """モーフ生成に最低限必要なボーンで不足しているボーンリストを取得する"""
        required_bone_names = {
            "センター",
            "上半身",
            "首",
            "頭",
            "左目",
            "右目",
            "両目",
        }
        missing_bone_names = sorted(list(required_bone_names - set(model.bones.names)))
        if missing_bone_names:
            raise MApplicationException(
                "モデルの表情生成に必要なボーンが不足しています。\n不足ボーン: {b}",
                b=", ".join(missing_bone_names),
            )

    def valid_motion(self, original_motion: VmdMotion) -> VmdMotion:
        """モーフ生成にあったモーションを取得する"""
        motion = original_motion.copy()

        return motion

    def get_bone_matrixes(self, model: PmxModel) -> VmdBoneFrameTrees:
        """初期姿勢での各ボーンの位置を求める"""
        bone_matrixes = VmdMotion().animate_bone([0], model)
        return bone_matrixes

    def check_blend(self, model: PmxModel) -> dict[tuple[int, int], "DuplicateMorph"]:
        logger.info("モーフブレンドチェック", decoration=MLogger.Decoration.LINE)

        model.update_vertices_by_bone()

        morph_vertices: dict[int, dict[int, list[np.ndarray]]] = {}

        # 各モーフで動く頂点リストと変動量を取得
        for morph in model.morphs:
            logger.count("モーフ変動量", index=morph.index, total_index_count=len(model.morphs), display_block=10)

            if morph.morph_type not in [MorphType.VERTEX, MorphType.BONE]:
                continue

            if morph.morph_type == MorphType.VERTEX:
                # 頂点モーフの場合、頂点INDEXと変動量だけ保持
                morph_vertices[morph.index] = {}
                for offset in morph.offsets:
                    vertex_offset: VertexMorphOffset = offset
                    morph_vertices[morph.index][vertex_offset.vertex_index] = [
                        (vertex_offset.position * (r * 0.1)).vector for r in range(1, 11)
                    ]

            elif morph.morph_type == MorphType.BONE:
                morph_vertices[morph.index] = {}

                for r in range(1, 11):
                    motion = VmdMotion()
                    motion.morphs[morph.name].append(VmdMorphFrame(0, morph.name, r * 0.1))
                    morph_matrixes = motion.animate_bone([0], model)

                    for offset in morph.offsets:
                        bone_offset: BoneMorphOffset = offset
                        bone_vertex_index = model.vertices_by_bones.get(bone_offset.bone_index, [])
                        if bone_vertex_index in morph_vertices[morph.index]:
                            continue

                        vertex = model.vertices[bone_vertex_index]
                        mat = np.zeros((4, 4))
                        for bone_index, bone_weight in zip(vertex.deform.indexes, vertex.deform.weights):
                            mat += morph_matrixes[0, model.bones[bone_index].name].local_matrix.vector * bone_weight
                        # 変形後の頂点位置の差分を保持
                        morph_vertices[morph.index][bone_vertex_index].append((MMatrix4x4(mat) * MVector3D()).vector)

        morph_duplicate_choices: dict[tuple[int, int], DuplicateMorph] = {}
        morph_keys = list(morph_vertices.keys())
        total_morph_count = len(morph_keys) * len(morph_keys)
        for i, (morph1_index, morph2_index) in enumerate(product(morph_keys, repeat=2)):
            logger.count("モーフ破綻チェック", index=i, total_index_count=total_morph_count, display_block=100)

            if morph1_index == morph2_index:
                continue

            morph1 = model.morphs[morph1_index]
            morph2 = model.morphs[morph2_index]

            morph1_vertices = morph_vertices[morph1_index]
            morph2_vertices = morph_vertices[morph2_index]

            duplicate_vertex_indexes = set(list(morph1_vertices.keys())) & set(list(morph2_vertices.keys()))
            if not duplicate_vertex_indexes:
                # 重複が無い場合、スルー
                continue

            morph1_vertex_positions = np.array([morph1_vertices[vidx] for vidx in duplicate_vertex_indexes])
            morph2_vertex_positions = np.array([morph2_vertices[vidx] for vidx in duplicate_vertex_indexes])

            min_vertex_positions = np.min(np.hstack((morph1_vertex_positions, morph2_vertex_positions)), axis=1)
            max_vertex_positions = np.max(np.hstack((morph1_vertex_positions, morph2_vertex_positions)), axis=1)

            for r1, r2 in product(range(10), repeat=2):
                morph1_ratio_vertex_positions = morph1_vertex_positions[:, r1, :]
                morph2_ratio_vertex_positions = morph2_vertex_positions[:, r2, :]

                ratio1 = (r1 * 0.1) + 0.1
                ratio2 = (r2 * 0.1) + 0.1
                max_duplicate_vertices = np.where(
                    morph1_ratio_vertex_positions + morph2_ratio_vertex_positions > max_vertex_positions * 1.2
                )
                min_duplicate_vertices = np.where(
                    morph1_ratio_vertex_positions + morph2_ratio_vertex_positions < min_vertex_positions * 1.2
                )
                if min(len(list(morph1_vertices.keys())), len(list(morph2_vertices.keys()))) * 0.1 < len(
                    np.unique(min_duplicate_vertices[0])
                ) + len(np.unique(max_duplicate_vertices[0])):
                    # 最大の一定量を一定個数の頂点が超えてる場合、破綻する可能性があると見なす
                    # logger.debug(
                    #     f"破綻危険性あり m1[{morph1.name}({ratio1:.1f})], m2[{morph2.name}({ratio2:.1f})], "
                    #     + f"min[{np.unique(min_duplicate_vertices[0]).shape}], min[{np.unique(max_duplicate_vertices[0]).shape}]"
                    # )

                    # 重複頂点INDEXリスト
                    if (morph1_index, morph2_index) not in morph_duplicate_choices:
                        morph_duplicate_choices[(morph1_index, morph2_index)] = DuplicateMorph(
                            morph1_index, morph1.name, morph2_index, morph2.name, list(duplicate_vertex_indexes)
                        )
                    morph_duplicate_choices[(morph1_index, morph2_index)].append(ratio1, ratio2)

                # logger.debug(f"破綻なし m1[{morph1.name}({ratio1:.1f})], m2[{morph2.name}({ratio2:.1f})]")

        return morph_duplicate_choices

    def get_blink_conditions(self) -> dict[str, float]:
        return BLINK_CONDITIONS


class DuplicateMorph:
    def __init__(
        self,
        morph1_index: int,
        morph1_name: str,
        morph2_index: int,
        morph2_name: str,
        duplicate_vertex_indexes: list[int],
    ) -> None:
        self.morph1_index = morph1_index
        self.morph1_name = morph1_name
        self.morph2_index = morph2_index
        self.morph2_name = morph2_name
        self.duplicate_vertex_indexes = duplicate_vertex_indexes
        self.ratios: list[tuple[float, float]] = []
        self.choice_name = f"1[{morph1_name}] - 2[{morph2_name}]"

    def append(self, morph1_ratio: float, morph2_ratio: float):
        self.ratios.append((morph1_ratio, morph2_ratio))
