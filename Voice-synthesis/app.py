import os
from os.path import exists, join, basename, splitext
import sys
sys.path.append(join('tacotron2', 'waveglow/'))
sys.path.append('tacotron2')
import time
import matplotlib
import matplotlib.pylab as plt
import numpy as np
import torch

from hparams import create_hparams
from model import Tacotron2
from layers import TacotronSTFT
from audio_processing import griffin_lim
from text import text_to_sequence
from denoiser import Denoiser

from flask import Flask, jsonify, request
import requests
from flask_restful import Api,Resource
import google.cloud.storage as gcs
from scipy.io.wavfile import write

hparams = create_hparams()
hparams.sampling_rate = 22050 
hparams.max_decoder_steps = 6000 # How long the audio will be before it cuts off (1000 is about 11 seconds)
hparams.gate_threshold = 0.1 # Model must be 90% sure the clip is over before ending generation (the higher this number is, the more likely that the AI will keep generating until it reaches the Max Decoder Steps)

# Load WaveGlow
waveglow = torch.load('waveglow.pt')['model']
waveglow.cuda().eval().half()
for k in waveglow.convinv:
    k.float()
denoiser = Denoiser(waveglow)

app = Flask(__name__)
api = Api(app)

def synthesize_voice(text,object_id,user_model,denoise_strength=10.0):
    
    sigma = 0.8
    raw_input = True # disables automatic ARPAbet conversion, useful for inputting your own ARPAbet pronounciations or just for testing
    
    # initialize Tacotron2 with the pretrained model
    model = Tacotron2(hparams)
    model.load_state_dict(torch.load(user_model)['state_dict'])
    _ = model.cuda().eval().half()
    
    for i in text.split("\n"):
        if len(i) < 1: 
            continue
        
        if raw_input:
            if i[-1] != ";": 
                i=i+";" 
        
        with torch.no_grad(): # save VRAM by not including gradients
            sequence = np.array(text_to_sequence(i, ['english_cleaners']))[None, :]
            sequence = torch.autograd.Variable(torch.from_numpy(sequence)).cuda().long()
            mel_outputs, mel_outputs_postnet, _, alignments = model.inference(sequence)

            audio = waveglow.infer(mel_outputs_postnet, sigma=sigma)[0].data.cpu().numpy()
            write(f'static/{object_id}.wav', rate = hparams.sampling_rate , data = audio.astype(np.float32))

def cut_spaces(string):
    string_after = ''.join(string.split(" "))
    return string_after

class Synthesize(Resource):
    def post(self):
        data = request.get_json()
        user_id = data['user_id']
        object_id = data['object_id']
        user_text = data['user_text']
        user_model = data['user_model']
        
        user_id = cut_spaces(user_id)
        object_id = cut_spaces(object_id)
        
        synthesize_voice(text=user_text,object_id=object_id,user_model=user_model)

        gcs_client = gcs.Client()
        bucket_name = 'deepthank-audio-customer'
        bucket = gcs_client.get_bucket(f'{bucket_name}')
        try:
            blob = bucket.blob(f'{object_id}/{object_id}.wav')
            blob.upload_from_filename(f'static/{object_id}.wav',content_type='audio/wav')

            jsontext = {
                'user_id' : user_id,
                'audio_url' : f'https://storage.googleapis.com/{bucket_name}/{user_id}/{object_id}.wav',
                'status' : 200
            }

            return jsonify(jsontext)
        
        except:

            jsontext = {
                'user_id' : user_id,
                'audio_url' : None,
                'status' : 500
            }

            return jsonify(jsontext)

api.add_resource(Synthesize,'/api/audio_synthesize')

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')