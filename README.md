To run: `python vsiConverter.py sample.vsi`

Once run, a WireMock OSS project folder will be created based on the name of the VSI file provided on the command line.
Drag and drop this project folder into the WireMock Cloud import dialog.

Tested against python v 3.11.5

To Do:
* Test against more VSI examples
* Add logic to detect REST vs XML
* Add logic to switch between XPATH and JSONPATH WMC handlebar helpers
* Add logic to apply proper response header based on REST vs XML