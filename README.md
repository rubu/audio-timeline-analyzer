# Description #

This is a python script for analyzing input / output timeline csv files from Sonarworks Reference 4, to understand clock drift issues and causes for audio clicks and pops.

# Setup #

## With pipenv ##

* Install pipenv with `pip install pipenv`
* Run `pipenv install` in the repo folder to install the needed python packages.
* Run `pipenv shell` to activate the virutalenv

## Manual package installation ##

* On Windows `pip install pandas xlsxwriter numpy==1.19.3` (newer numpy versions fail with an error that they violate windows runtime checks)
* On macOS `pip install pandas xlsxwriter numpy` 

# Usage #

Run audio-timeline-analyzer.py with arguments `-i <path to the input timeline>`, for example:
* macOS: `audio-timeline-analyzer.py -i "./samples/just spotify 44109/InputTimeline-1605095046.csv"` 
* Windows: `audio-timeline-analyzer.py -i "samples\just spotify 44109\InputTimeline-1605095046.csv"`
The script expects to find a file name `OutputTimeline-1605095046.csv` in the same folder to read the ouput timings from. After that a file called `timeline.xlsx` will be created
in the directory the script was invoked from containing the processed data in the Timeline page, and a chart showing the clock dritfs in Sample Rate Drift page.