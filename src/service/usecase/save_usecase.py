import os

from mlib.base.logger import MLogger
from mlib.pmx.pmx_collection import PmxModel
from mlib.vmd.vmd_collection import VmdMotion
from mlib.vmd.vmd_writer import VmdWriter

logger = MLogger(os.path.basename(__file__))
__ = logger.get_text


class SaveUsecase:
    def save(
        self,
        model: PmxModel,
        motion: VmdMotion,
        output_path: str,
    ) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        VmdWriter(motion, output_path, model.name).save()
