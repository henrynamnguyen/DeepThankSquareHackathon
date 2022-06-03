# **Wav2Lip**: *Accurately Lip-syncing Videos In The Wild*
----------
**Highlights**
----------
 - Lip-sync videos to any target speech with high accuracy :100:. Try our [interactive demo](https://bhaasha.iiit.ac.in/lipsync).
 - :sparkles: Works for any identity, voice, and language. Also works for CGI faces and synthetic voices.
 - Complete training code, inference code, and pretrained models are available :boom:
 - Or, quick-start with the Google Colab Notebook: [Link](https://colab.research.google.com/drive/1tZpDWXz49W6wDcTprANRGLo2D_EbD5J8?usp=sharing). Checkpoints and samples are available in a Google Drive [folder](https://drive.google.com/drive/folders/1I-0dNLfFOSFwrfqjNa-SXuwaURHE5K4k?usp=sharing) as well. There is also a [tutorial video](https://www.youtube.com/watch?v=Ic0TBhfuOrA) on this, courtesy of [What Make Art](https://www.youtube.com/channel/UCmGXH-jy0o2CuhqtpxbaQgA). Also, thanks to [Eyal Gruss](https://eyalgruss.com), there is a more accessible [Google Colab notebook](https://j.mp/wav2lip) with more useful features. 
 - :fire: :fire: Several new, reliable evaluation benchmarks and metrics [[`evaluation/` folder of this repo]](https://github.com/Rudrabha/Wav2Lip/tree/master/evaluation) released. Instructions to calculate the metrics reported in the paper are also present.

Prerequisites
-------------
- `Python 3.6` 
- ffmpeg: `sudo apt-get install ffmpeg`
- Install necessary packages using `pip install -r requirements.txt`. Alternatively, instructions for using a docker image is provided [here](https://gist.github.com/xenogenesi/e62d3d13dadbc164124c830e9c453668). Have a look at [this comment](https://github.com/Rudrabha/Wav2Lip/issues/131#issuecomment-725478562) and comment on [the gist](https://gist.github.com/xenogenesi/e62d3d13dadbc164124c830e9c453668) if you encounter any issues. 
- Face detection [pre-trained model](https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth) should be downloaded to `face_detection/detection/sfd/s3fd.pth`. Alternative [link](https://iiitaphyd-my.sharepoint.com/:u:/g/personal/prajwal_k_research_iiit_ac_in/EZsy6qWuivtDnANIG73iHjIBjMSoojcIV0NULXV-yiuiIg?e=qTasa8) if the above does not work.


