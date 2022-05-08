from flask import Flask,jsonify,request
from flask_restful import Api,Resource
from google.cloud.storage import bucket
import requests
import google.cloud.storage as gcs
import os
import subprocess

FILE_PATH = '/app/'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key1.json'
app = Flask(__name__)
api = Api(app)

#Helper functions
def filetype(url):
    type = str(url).split('.')[-1]
    return type

def allowed_video_filetype(video_url):
    type = filetype(url=video_url)
    if type not in ['mp4','png','jpg','jpeg','mov','ogg','webm']:
        return False
    else:
        return True

def allowed_audio_filetype(audio_url):
    type = filetype(url=audio_url)
    if type not in ['mp3','wav','mp4','ogg','mpeg','webm']:
        return False
    else:
        return True

def clean_up_after(success,user_id,object_id,video_url,audio_url):
    if success:
        os.remove(FILE_PATH + f'temp/{user_id}{object_id}temp_video.{filetype(url=video_url)}')
        os.remove(FILE_PATH + f'temp/{user_id}{object_id}temp_audio.{filetype(url=audio_url)}')
        os.remove(FILE_PATH + f'results/{user_id}{object_id}result.mp4')
        os.remove(FILE_PATH + f'temp/result.avi')
    else:
        os.remove(FILE_PATH + f'temp/{user_id}{object_id}temp_video.{filetype(url=video_url)}')
        os.remove(FILE_PATH + f'temp/{user_id}{object_id}temp_audio.{filetype(url=audio_url)}')

#this function is to check if an input has any spaces inside its name and cut them
def cut_spaces(string):
    string_after = ''.join(string.split(" "))
    return string_after

class Lipsync(Resource):
    def post(self):
        data = request.get_json()
        user_id = data['user_id']
        object_id = data['object_id']
        video_url = data['video_url']
        audio_url = data['audio_url']

        #check some pre-conditions for input
        user_id = cut_spaces(user_id)
        object_id = cut_spaces(object_id)
        if not allowed_video_filetype(video_url=video_url) or not allowed_audio_filetype(audio_url=audio_url):
            jsontext = {
                'user_id':user_id,
                'processed_video_url':None,
                'message':'not allowed file type',
                'status': 401
            }
            return jsonify(jsontext)

        #Download video to process lipsync
        video_data = requests.get(video_url)
        video = video_data.content
        f = open(f'temp/{user_id+object_id}temp_video.{filetype(url=video_url)}','wb')
        f.write(video)
        f.close()
        
        #Download audio to process lipsync
        audio_data = requests.get(audio_url)
        audio = audio_data.content
        g = open(f'temp/{user_id+object_id}temp_audio.{filetype(url=audio_url)}','wb')
        g.write(audio)
        g.close()
     
        #begin the lipsync
        try:
            subprocess.run(f'python3 inference.py --checkpoint_path wav2lip_gan.pth --face temp/{user_id+object_id}temp_video.{filetype(url=video_url)} --audio temp/{user_id+object_id}temp_audio.{filetype(url=audio_url)} --outfile results/{user_id+object_id}result.mp4',shell=True)
            
            gcs_client = gcs.Client()
            processed_video_bucket_name = 'deepthank-processed-video-customer'
            processed_video_bucket = gcs_client.get_bucket(processed_video_bucket_name)
            processed_video_blob = processed_video_bucket.blob(f'{user_id}/{object_id}.mp4')
            processed_video_blob.upload_from_filename(f'results/{user_id+object_id}result.mp4',content_type='video/mp4')
            
            jsontext = {
                'user_id' : user_id,
                'processed_video_url': f'https://storage.googleapis.com/deepthank-processed-video-customer/{user_id}/{object_id}.mp4',
                'status': 200
            }

            clean_up_after(success=True,user_id=user_id,object_id=object_id,video_url=video_url,audio_url=audio_url)

            return jsonify(jsontext)
        #incase lipsync fails
        except:

            jsontext = {
                'user_id': user_id,
                'processed_video_url': None,
                'message':'Cannot lipsync',
                'status': 500
            }

            clean_up_after(success=False,user_id=user_id,object_id=object_id,video_url=video_url,audio_url=audio_url)

            return jsonify(jsontext)

#this class is for testing network purpose only
class Hello(Resource):
    def get(self):
        return 'Hello there. Succeeded.'

api.add_resource(Lipsync,'/lipsync')
api.add_resource(Hello,'/lipsync/hello')

if __name__ == '__main__':
    app.run(host='0.0.0.0')