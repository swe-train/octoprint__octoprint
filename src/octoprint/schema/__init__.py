__license__ = "GNU Affero General Public License http://www.gnu.org/licenses/agpl.html"
__copyright__ = "Copyright (C) 2022 The OctoPrint Project - Released under terms of the AGPLv3 License"

from pydantic import BaseModel as PydanticBaseModel

try:
    # Python 3.8+
    from typing import Literal  # noqa: F401
except ImportError:
    # Python 3.7
    from typing_extensions import Literal  # noqa: F401


class BaseModel(PydanticBaseModel):
    class Config:
        use_enum_values = True
