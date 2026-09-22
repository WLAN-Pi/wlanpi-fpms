import sys

import fakes

# Several fpms modules import page/display helpers that in turn pull in Pi-only
# hardware libraries (luma, spidev, ...). Replace those helper modules with the
# recording fakes before the modules under test are imported, so the suite can
# run on CI without the hardware dependencies.
_FAKE_MODULES = (
    "fpms.modules.pages.alert",
    "fpms.modules.pages.display",
    "fpms.modules.pages.pagedtable",
    "fpms.modules.pages.simpletable",
)

for _module in _FAKE_MODULES:
    sys.modules.setdefault(_module, fakes)
