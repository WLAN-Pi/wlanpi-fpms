import sys

import fakes

_FAKE_MODULES = (
    "fpms.modules.pages.alert",
    "fpms.modules.pages.display",
    "fpms.modules.pages.pagedtable",
    "fpms.modules.pages.simpletable",
    "fpms.modules.wlanpi_oled",
)

for _module in _FAKE_MODULES:
    sys.modules.setdefault(_module, fakes)
