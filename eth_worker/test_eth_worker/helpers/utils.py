
# Just a randomly generated key. Needless to say, DON'T USE THIS FOR REAL FUNDS ANYWHERE
import uuid
from typing import cast

from sempo_types import UUID

pk = '0x2bd62cccd89e375b2c248eaa123dc24141f7a8c6e384e045c0698ebaa1d62922'
address = '0x468F90c5a236130E5D51260A2A5Bfde834C694b6'


def str_uuid() -> UUID:
    return cast(UUID, str(uuid.uuid4()))