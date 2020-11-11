# Description #

This is a python script for analyzing input / output timeline csv files from Sonarworks Reference 4, to understand clock drift issues and causes for audio clicks and pops.
 
# Setup #

After cloning the repo run `pipenv install` to install the needed python packages.

# Usage #

Run audio-timeline-analyzer.py with arguments `-i <path to the input timeline>`, for example `-i "./samples/just spotify 44109/InputTimeline-1605095046.csv"`. In this case the 
script expects to find a file name `OutputTimeline-1605095046.csv` in the same folder to read the ouput timings from. After that a file called `timeline.xlsx` will be created
in the directory the script was invoked from containing the processed data in the Timeline page, and a chart showing the clock dritfs in Sample Rate Drift page.