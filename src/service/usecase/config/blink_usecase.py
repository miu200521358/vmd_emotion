import os
from enum import Enum

import numpy as np

from mlib.base.interpolation import Interpolation, get_infections
from mlib.base.logger import MLogger
from mlib.base.math import MQuaternion, MVector2D, MVector3D
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_part import VmdBoneFrame, VmdMorphFrame

logger = MLogger(os.path.basename(__file__), level=1)
__ = logger.get_text

CLOSE_INTERPOLATION = Interpolation()
CLOSE_INTERPOLATION.start = MVector2D(60, 10)
CLOSE_INTERPOLATION.end = MVector2D(70, 120)


class BlinkUsecase:
    def create_blink(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_motion: VmdMotion,
        condition_probabilities: dict[str, float],
        linkage_depth: float,
        blink_span: int,
        eyebrow_below_name: str,
        blink_name: str,
        laugh_name: str,
    ) -> None:
        """まばたき生成"""

        # 既存キーフレ削除
        del motion.bones["右目"]
        del motion.bones["左目"]
        del motion.morphs[blink_name]
        del motion.morphs[eyebrow_below_name]

        # まばたきをする可能性があるキーフレ一覧
        # 手足の動きもキーフレを取る
        eye_fnos = sorted(
            set([bf.index for bone_name in model.bone_trees["両目"].names for bf in motion.bones[bone_name]]) | {motion.bones.max_fno}
        )

        logger.info("目線変動量取得", decoration=MLogger.Decoration.LINE)

        kick_probability = condition_probabilities[BlinkConditions.AFTER_KICK.value.name] * 0.01
        wrist_probability = condition_probabilities[BlinkConditions.WRIST_CROSS.value.name] * 0.01

        target_bone_names = ["両目"]
        if 0 < kick_probability:
            target_bone_names.extend(["左足首", "右足首"])
        if 0 < wrist_probability:
            target_bone_names.extend(["左手首", "右手首"])

        logger.info("両目変動量")
        eye_matrixes = motion.animate_bone(eye_fnos, model, target_bone_names, out_fno_log=True)

        prev_blink = None
        blink_vectors: list[MVector3D] = []
        blink_dots: list[float] = []
        upper_ratio_ys: list[float] = []
        left_ankle_ys: list[float] = []
        right_ankle_ys: list[float] = []
        left_wrist_distance_ratios: list[float] = []
        right_wrist_distance_ratios: list[float] = []
        for fidx, fno in enumerate(eye_fnos):
            logger.count("目線変動量取得", index=fidx, total_index_count=len(eye_fnos), display_block=100)
            eye_global_direction_vector = eye_matrixes[fno, "両目"].global_matrix * MVector3D(0, 0, -1)
            eye_vector = (eye_global_direction_vector - eye_matrixes[fno, "両目"].position).normalized() * -1
            upper_ratio_ys.append(eye_matrixes[fno, "上半身"].position.y / model.bones["上半身"].position.y)
            if 0 < kick_probability:
                left_ankle_ys.append(eye_matrixes[fno, "左足首"].position.y / model.bones["左ひざ"].position.y)
                right_ankle_ys.append(eye_matrixes[fno, "右足首"].position.y / model.bones["右ひざ"].position.y)
            if 0 < wrist_probability:
                left_wrist_distance_ratios.append(
                    eye_matrixes[fno, "左手首"].position.distance(eye_matrixes[fno, "両目"].position)
                    / model.bones["左手首"].position.distance(model.bones["左ひじ"].position)
                )
                right_wrist_distance_ratios.append(
                    eye_matrixes[fno, "右手首"].position.distance(eye_matrixes[fno, "両目"].position)
                    / model.bones["右手首"].position.distance(model.bones["右ひじ"].position)
                )

            if not prev_blink:
                # 初回はスルー
                prev_blink = eye_vector
                blink_dots.append(1.0)
                continue

            # 両目の向き
            blink_dot = eye_vector.dot(prev_blink)
            # logger.debug(f"fno[{fno:04d}], eye[{eye_global_direction_vector}], blink[{eye_vector}], dot[{blink_dot:.3f}]")

            blink_dots.append(blink_dot)
            blink_vectors.append(eye_vector)
            prev_blink = eye_vector

        blink_weight_fnos: dict[int, float] = {}
        blink_type_fnos: dict[int, str] = {}

        normal_probability = condition_probabilities[BlinkConditions.NORMAL.value.name] * 0.01
        if 0 < normal_probability:
            logger.info("まばたきポイント検出 [前のまばたきから一定時間経過した時]", decoration=MLogger.Decoration.LINE)

            normal_dots = get_infections(blink_dots, 0.02)
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=len(normal_dots))

            for fidx in normal_dots:
                # 動きがある箇所で、乱数条件を満たしている場合、登録対象
                rnd = np.random.rand()
                if rnd <= normal_probability:
                    fno = eye_fnos[fidx]
                    gaze_degrees = motion.bones["両目"][fno].rotation.to_euler_degrees()
                    if gaze_degrees.x < 1:
                        # 目線が上に向かってたらスルー
                        logger.debug(f"まばたきポイント[時間経過] [{eye_fnos[fidx]}][d={blink_dots[fidx]:.3f}][p={normal_probability:.3f}]")
                        blink_weight_fnos[fno] = 0.5
                        blink_type_fnos[fno] = __("前のまばたきから一定時間経過した時")

        if 0 < kick_probability:
            logger.info("まばたきポイント検出 [キックの着地後]", decoration=MLogger.Decoration.LINE)

            # ジャンプ（足首の動き）の箇所を抽出する
            kick_fidxs = sorted(
                set(np.where(np.array(left_ankle_ys) > 1.2)[0].tolist()) | set(np.where(np.array(right_ankle_ys) > 1.2)[0].tolist())
            )
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=len(kick_fidxs))

            for fidx in kick_fidxs:
                rnd = np.random.rand()
                if rnd <= kick_probability and fidx < len(eye_fnos) - 2:
                    # ジャンプの次の変曲点（着地とおぼしき場所）でまばたきを入れる
                    fno = eye_fnos[fidx + 1]
                    logger.debug(
                        f"まばたきポイント[キック] [{fno}][l={left_ankle_ys[fidx]:.3f}][r={right_ankle_ys[fidx]:.3f}][p={kick_probability:.3f}]"
                    )
                    blink_weight_fnos[fno] = 0.6
                    blink_type_fnos[fno] = __("キックの着地後")

        if 0 < wrist_probability:
            logger.info("まばたきポイント検出 [腕が顔の前を横切った時]", decoration=MLogger.Decoration.LINE)

            # ジャンプ（足首の動き）の箇所を抽出する
            wrist_fidxs = sorted(
                set(np.where(np.array(left_wrist_distance_ratios) < 0.6)[0].tolist())
                | set(np.where(np.array(right_wrist_distance_ratios) < 0.6)[0].tolist())
            )
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=len(wrist_fidxs))

            for fidx in wrist_fidxs:
                rnd = np.random.rand()
                if rnd <= wrist_probability and fidx < len(eye_fnos) - 1:
                    # 手首の変曲点（近付いたとおぼしき場所）でまばたきを入れる
                    fno = eye_fnos[fidx]
                    logger.debug(
                        f"まばたきポイント[手首] [{fno}][l={left_wrist_distance_ratios[fidx]:.3f}]"
                        + f"[r={right_wrist_distance_ratios[fidx]:.3f}][l={wrist_probability:.3f}]"
                    )
                    blink_weight_fnos[fno] = 0.6
                    blink_type_fnos[fno] = __("腕が顔の前を横切った時")

        jump_probability = condition_probabilities[BlinkConditions.AFTER_JUMP.value.name] * 0.01
        if 0 < jump_probability:
            logger.info("まばたきポイント検出 [ジャンプの着地後]", decoration=MLogger.Decoration.LINE)

            jump_fidxs = np.where(np.array(upper_ratio_ys) > 1.1)[0]
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=len(jump_fidxs))

            # ジャンプ（上半身のY位置が高い）の箇所を抽出する
            for fidx in jump_fidxs:
                rnd = np.random.rand()
                if rnd <= jump_probability and fidx < len(eye_fnos) - 2:
                    # ジャンプの次の変曲点（着地とおぼしき場所）でまばたきを入れる
                    fno = eye_fnos[fidx + 1]
                    logger.debug(f"まばたきポイント[ジャンプ] [{fno}][u={upper_ratio_ys[fidx]:.3f}][p={jump_probability:.3f}]")
                    blink_weight_fnos[fno] = 0.7
                    blink_type_fnos[fno] = __("ジャンプの着地後")

        turn_probability = condition_probabilities[BlinkConditions.TURN.value.name] * 0.01
        if 0 < turn_probability:
            logger.info("まばたきポイント検出 [ターンの開始時]", decoration=MLogger.Decoration.LINE)

            turn_fidxs = get_infections(blink_dots, 0.6)
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=len(turn_fidxs))

            for fidx in turn_fidxs:
                rnd = np.random.rand()
                if rnd <= turn_probability:
                    fno = eye_fnos[fidx]
                    logger.debug(f"まばたきポイント[ターン] [{fno}][d={blink_dots[fidx]:.3f}][p={turn_probability:.3f}]")
                    blink_weight_fnos[fno] = 0.8
                    blink_type_fnos[fno] = __("ターンの開始時")

        opening_probability = condition_probabilities[BlinkConditions.OPENING.value.name] * 0.01
        ending_probability = condition_probabilities[BlinkConditions.ENDING.value.name] * 0.01
        if 0 < opening_probability or 0 < ending_probability:
            logger.info("まばたきポイント検出 [モーションの開始・終了]", decoration=MLogger.Decoration.LINE)

            infection_fnos = get_infections(blink_dots, 0.2)
            logger.info("変曲点抽出 候補キーフレ[{d}件]", d=2)

            # 最初の変曲点までのキーフレ間が一定区間ある場合、登録対象
            rnd = np.random.rand()
            start_fno = eye_fnos[infection_fnos[0]]
            if 30 * 5 < start_fno and rnd <= opening_probability:
                logger.debug(f"まばたきポイント[開始] [{start_fno}][d={blink_dots[fidx]:.3f}][p={opening_probability:.3f}]")
                blink_weight_fnos[start_fno] = 0.9
                blink_type_fnos[fno] = __("モーションの開始")

            # 最後の変曲点までのキーフレ間が一定区間ある場合、登録対象
            rnd = np.random.rand()
            end_fno = motion.max_fno - eye_fnos[infection_fnos[-1]]
            if 30 * 5 < end_fno and rnd <= ending_probability:
                logger.debug(f"まばたきポイント[終了] [{end_fno}][d={blink_dots[fidx]:.3f}][p={ending_probability:.3f}]")
                blink_weight_fnos[end_fno] = 0.9
                blink_type_fnos[fno] = __("モーションの終了")

        logger.info("まばたき生成", decoration=MLogger.Decoration.LINE)

        eyebrow_below_ratio = linkage_depth * 0.5
        close_qq = MQuaternion.from_euler_degrees(linkage_depth * -10, 0, 0)
        start_double_qq = MQuaternion.from_euler_degrees(linkage_depth * -5, 0, 0)

        nums = 0
        # 最初のまばたきを対象とする
        fno = sorted(blink_weight_fnos.keys())[0]
        is_double_before = False
        is_double_after = False
        prev_fno = start_fno = close_fno = weight_fno = open_fno = end_fno = 0
        range_fnos: dict[int, float] = {}
        while prev_fno < eye_fnos[-1]:
            # 重み付けをしたまばたき -----------
            weight = blink_weight_fnos.get(fno, 0.3)
            blink_type = blink_type_fnos.get(fno, __("連続"))
            weight_blink = round(1.5 * weight)

            # ランダムで二回連続の瞬きをする
            if not is_double_before and not is_double_after and np.random.rand() < 0.2:
                is_double_before = True
                is_double_after = False
            else:
                is_double_before = False

            # 最初は静止 (二重まばたきの場合は半開き)
            start_fno = fno - weight_blink - 4 + np.random.randint(-1, 1)
            mf1 = VmdMorphFrame(start_fno, blink_name)
            mf1.ratio = 0.2 if is_double_after else 0.0
            motion.morphs[blink_name].append(mf1)
            output_motion.morphs[blink_name].append(mf1.copy())

            # 閉じる
            close_fno = fno - weight_blink - 1
            mf2 = VmdMorphFrame(close_fno, blink_name)
            mf2.ratio = 1.0
            motion.morphs[blink_name].append(mf2)
            output_motion.morphs[blink_name].append(mf2.copy())

            # 停止
            weight_fno = fno
            mf3 = VmdMorphFrame(weight_fno, blink_name)
            mf3.ratio = 1.0
            motion.morphs[blink_name].append(mf3)
            output_motion.morphs[blink_name].append(mf3.copy())

            if not is_double_before:
                # 半開き
                open_fno = fno + weight_blink + 2 + np.random.randint(-1, 1)
                mf4 = VmdMorphFrame(open_fno, blink_name)
                mf4.ratio = 0.5
                motion.morphs[blink_name].append(mf4)
                output_motion.morphs[blink_name].append(mf4.copy())

                # 開く (二重まばたきの場合はスルー)
                end_fno = fno + weight_blink + 6 + np.random.randint(-1, 1)
                mf5 = VmdMorphFrame(end_fno, blink_name)
                mf5.ratio = 0.0
                motion.morphs[blink_name].append(mf5)
                output_motion.morphs[blink_name].append(mf5.copy())

            # 眉を下げる -------

            bmf1 = VmdMorphFrame(start_fno - 1, eyebrow_below_name)
            bmf1.ratio = 0.2 if is_double_after else 0.0
            motion.morphs[eyebrow_below_name].append(bmf1)
            output_motion.morphs[eyebrow_below_name].append(bmf1.copy())

            bmf2 = VmdMorphFrame(close_fno - 1, eyebrow_below_name)
            bmf2.ratio = eyebrow_below_ratio
            motion.morphs[eyebrow_below_name].append(bmf2)
            output_motion.morphs[eyebrow_below_name].append(bmf2.copy())

            if not is_double_before:
                bmf3 = VmdMorphFrame(open_fno + 1, eyebrow_below_name)
                bmf3.ratio = eyebrow_below_ratio
                motion.morphs[eyebrow_below_name].append(bmf3)
                output_motion.morphs[eyebrow_below_name].append(bmf3.copy())

                bmf4 = VmdMorphFrame(end_fno + 1, eyebrow_below_name)
                bmf4.ratio = 0.0
                motion.morphs[eyebrow_below_name].append(bmf4)
                output_motion.morphs[eyebrow_below_name].append(bmf4.copy())

            # 閉じるのに合わせて目線を下に ---------

            # 最初は静止
            start_left_bf = VmdBoneFrame(start_fno - 1, "左目")
            if is_double_after:
                start_left_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
                start_left_bf.rotation = start_double_qq.copy()
            motion.bones["左目"].append(start_left_bf)
            output_motion.bones["左目"].append(start_left_bf.copy())

            start_right_bf = VmdBoneFrame(start_fno - 1, "右目")
            if is_double_after:
                start_right_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
                start_right_bf.rotation = start_double_qq.copy()
            motion.bones["右目"].append(start_right_bf)
            output_motion.bones["右目"].append(start_right_bf.copy())

            # 閉じるよりも少し後に目を下に
            close_left_bf = VmdBoneFrame(close_fno - 1, "左目")
            close_left_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
            close_left_bf.rotation = close_qq.copy()
            motion.bones["左目"].append(close_left_bf)
            output_motion.bones["左目"].append(close_left_bf.copy())

            close_right_bf = VmdBoneFrame(close_fno - 1, "右目")
            close_right_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
            close_right_bf.rotation = close_qq.copy()
            motion.bones["右目"].append(close_right_bf)
            output_motion.bones["右目"].append(close_right_bf.copy())

            # 開くのより少し後まで目を下に
            weight_left_bf = VmdBoneFrame(weight_fno + 2, "左目")
            weight_left_bf.rotation = close_qq.copy()
            motion.bones["左目"].append(weight_left_bf)
            output_motion.bones["左目"].append(weight_left_bf.copy())

            weight_right_bf = VmdBoneFrame(weight_fno + 2, "右目")
            weight_right_bf.rotation = close_qq.copy()
            motion.bones["右目"].append(weight_right_bf)
            output_motion.bones["右目"].append(weight_right_bf.copy())

            if not is_double_before:
                # 最後は元に戻す
                end_left_bf = VmdBoneFrame(end_fno - 2, "左目")
                end_left_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
                motion.bones["左目"].append(end_left_bf)
                output_motion.bones["左目"].append(end_left_bf.copy())

                end_right_bf = VmdBoneFrame(end_fno - 2, "右目")
                end_right_bf.interpolations.rotation = CLOSE_INTERPOLATION.copy()
                motion.bones["右目"].append(end_right_bf)
                output_motion.bones["右目"].append(end_right_bf.copy())

            logger.debug(
                f"まばたき[{weight}(DB:{is_double_before}, DA:{is_double_after})] start[{start_fno}], close[{close_fno}], "
                + f"weight[{weight_fno}], open[{open_fno}], end[{end_fno}]"
            )
            logger.info("-- まばたき生成 [キーフレ: {f}][種類: {t}]", f=weight_fno, t=blink_type)

            prev_fno = fno
            nums += 1

            # 前のキーフレから100F (3秒近く)分を抽出
            range_fnos = {}
            n = 1
            while not range_fnos:
                range_fnos = dict(
                    [
                        (f, blink_weight_fnos[f])
                        for f in sorted(blink_weight_fnos.keys())
                        if prev_fno + blink_span < f < prev_fno + ((blink_span + 100) * n)
                    ]
                )
                n += 1
                if n > 5:
                    prev_fno = eye_fnos[-1]
                    break

            if prev_fno < eye_fnos[-1]:
                # 範囲の中で最も重いまばたきを抽出する（同じのがある場合は前のを優先）
                # ランダムで二回連続の瞬きをする
                if is_double_before:
                    fno = weight_fno + 7
                    is_double_before = False
                    is_double_after = True
                else:
                    is_double_before = False
                    if is_double_after:
                        is_double_after = False
                    fno = list(range_fnos.keys())[int(np.argmax(list(range_fnos.values())))]


class BlinkCondition:
    def __init__(
        self,
        name: str,
        probability: float,
    ) -> None:
        """
        まばたきの条件
        name: 条件名(翻訳後を保持)
        ratio: デフォルト発生確率
        """
        self.name = __(name)
        self.probability = probability


class BlinkConditions(Enum):
    """まばたき条件リスト"""

    OPENING = BlinkCondition(name="モーションの開始", probability=100)
    ENDING = BlinkCondition(name="モーションの終了", probability=100)
    TURN = BlinkCondition(name="ターンの開始時", probability=100)
    AFTER_JUMP = BlinkCondition(name="ジャンプの着地後", probability=100)
    AFTER_KICK = BlinkCondition(name="キックの着地後", probability=0)
    WRIST_CROSS = BlinkCondition(name="腕が顔の前を横切った時", probability=80)
    NORMAL = BlinkCondition(name="前のまばたきから一定時間経過した時", probability=50)


BLINK_CONDITIONS: dict[str, float] = dict([(bs.value.name, bs.value.probability) for bs in BlinkConditions])
"""まばたき条件の名前と発生確率の辞書"""
