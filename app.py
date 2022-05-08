from logging import debug
from flask import Flask
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = 'henrynamnguyen'
app.config['UPLOAD_FOLDER'] = 'static/upload_files'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key1.json'

from campaign import campaign
app.register_blueprint(campaign,url_prefix='/')


if __name__ == '__main__':
    app.run(debug=True)






    

