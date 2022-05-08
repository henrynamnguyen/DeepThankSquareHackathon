FROM nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04

RUN export DEBIAN_FRONTEND=noninteractive RUNLEVEL=1 ; \
     apt-get update && apt-get install -y --no-install-recommends \
          build-essential cmake git curl ca-certificates \
          vim \
          python3-pip python3-dev python3-wheel \
          libglib2.0-0 libxrender1 python3-soundfile \
          ffmpeg && \
	rm -rf /var/lib/apt/lists/* && \
     pip3 install --upgrade setuptools

COPY . /app/
WORKDIR /app

RUN pip3 install --upgrade pip
RUN pip3 install \
  https://download.pytorch.org/whl/cu100/torch-1.1.0-cp36-cp36m-linux_x86_64.whl \
  -r requirements.txt
RUN mkdir -p /root/.cache/torch/checkpoints && \
     curl -SL -o /root/.cache/torch/checkpoints/s3fd-619a316812.pth "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"

CMD ["gunicorn","-w","3","-b",":5000","-t","360","wsgi:app"]