from flask import Blueprint, render_template, flash, request, jsonify, redirect, url_for, session
import json
from google.api_core.gapic_v1 import method
import google.cloud.storage as gcs
import google.cloud.firestore as gcfs
import requests
from werkzeug.utils import secure_filename
import os 
from square.client import Client
import uuid
from dotenv import load_dotenv


load_dotenv()

environment = os.getenv('SQ_ENVIRONMENT').lower()
application_id = os.getenv('SQ_APPLICATION_ID')
application_secret = os.getenv('SQ_APPLICATION_SECRET')
square_client = Client(environment=environment)
base_url = "https://connect.squareup.com" if environment == "production" else "https://connect.squareupsandbox.com"

#Initiate Cloud Firestore and Cloud Storage
db = gcfs.Client()
gcs_client = gcs.Client()

campaign = Blueprint('campaign',__name__)
ALLOWED_EXTENSIONS = {'mp4','jpeg','jpg','png'}

@campaign.route('/', methods = ['GET'])
def sign_up():
    oauth_authorize_url = "{0}/oauth2/authorize?client_id={1}&scope=CUSTOMERS_WRITE+CUSTOMERS_READ+ONLINE_STORE_SITE_READ+ORDERS_READ+ONLINE_STORE_SNIPPETS_WRITE+ONLINE_STORE_SNIPPETS_READ+PAYMENTS_READ+PAYMENTS_WRITE".format(base_url,application_id)
    content = """
    <div class="container" style="position: absolute;
    width: 300px;
    height: 200px;
    z-index: 15;
    top: 50%;
    left: 50%;
    margin: -100px 0 0 -150px;
    text-align: center;">
        
        <img src="https://storage.googleapis.com/memekit/deepthank-logo%20(1).png" width="280px">
        <a href="{0}"><button class="btn btn-light" style="margin-top: 30px;">Sign Up</button></a>
        
    </div>
    """.format(oauth_authorize_url)
    return render_template('sign-up.html',content=content)

#Helper function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_sites(environment='production',access_token='EAAAEPEYWjqA0uVhsGlGuoI5RqiJbaoJu3gtCIHmbvV0lxLe0WXfnR5TKrYSxk9E'):
    square_client = Client(environment=environment, access_token=access_token)
    sites = square_client.sites.list_sites()
    sites = sites.text
    sites_dict = json.loads(sites)
    return sites_dict['sites']



@campaign.route('/campaign',methods=['GET'])
def get_page():
    authorization_code = request.args.get('code')

    body = {}
    body['client_id'] = application_id
    body['client_secret'] = application_secret
    body['code'] = authorization_code
    body['grant_type'] = 'authorization_code'
    body['scopes'] = ['CUSTOMERS_WRITE','CUSTOMERS_READ','ONLINE_STORE_SITE_READ','ORDERS_READ','ONLINE_STORE_SNIPPETS_WRITE','ONLINE_STORE_SNIPPETS_READ','PAYMENTS_READ']
    
    square_client = Client(environment=environment)
    obtain_token = square_client.o_auth.obtain_token
    oauth_response = obtain_token(body)
    if oauth_response.is_success():
        user_id = oauth_response.body['merchant_id']
        access_token = oauth_response.body['access_token']
        session['user_id'] = user_id
        session['access_token'] = access_token
        
        #Save token to Firestore
        db.collection(user_id).document('access_token').set({
            'access_token' : access_token,
            'refresh_token' : oauth_response.body['refresh_token'],
            'expires_at' : oauth_response.body['expires_at']
        })
        
        #Get user sites
        site_id = ''
        sites_dict = get_user_sites()
        for site in sites_dict:
            site_id = site_id + """<option value="""+site['id']+""">"""+site['site_title']+"""</option>"""
        session['site_id_list_content'] = site_id
    elif oauth_response.is_error():
        print(oauth_response.errors)
    return render_template('campaign.html',enable_helper_buttons=False,site_id=session['site_id_list_content'])

#helper function
def process_user_text_snippet(user_text,environment,access_token):
    square_client = Client(environment=environment,access_token=access_token)
    try: 
        payments_list = square_client.payments.list_payments()
        payments_list = payments_list.text
        payments_list_dict = json.loads(payments_list)
        try:
            number_of_purchases = str(len(payments_list_dict['payments']))
            user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases)
        except:
            number_of_purchases = 'many'
            user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases)
        finally:
            try:
                last_customer_city = str(payments_list_dict['payments'][0]['shipping_address']['locality'])
                user_text = user_text.replace('LAST_CUSTOMER_CITY',last_customer_city)
            except:
                last_customer_city = 'your city'
                user_text = user_text.replace('LAST_CUSTOMER_CITY',last_customer_city)
            finally:
                order = square_client.orders.retrieve_order(order_id=payments_list_dict['payments'][0]['order_id'])
                order = order.text
                order_dict = json.loads(order)
                try:
                    last_customer_item = order_dict['order']['line_items'][0]['name']
                    user_text = user_text.replace('LAST_CUSTOMER_ITEM',last_customer_item)
                except:
                    last_customer_item = 'something'
                    user_text = user_text.replace('LAST_CUSTOMER_ITEM',last_customer_item)
                finally:
                    try:
                        last_customer_name = order_dict['order']['fulfillments'][0]['shipment_details']['recipient']['display_name'].split(' ')[0]
                        user_text = user_text.replace('LAST_CUSTOMER_NAME',last_customer_name)
                    except:
                        try:
                            last_customer_name = payments_list_dict['payments'][0]['shipping_address']['first_name']
                            user_text = user_text.replace('LAST_CUSTOMER_NAME',last_customer_name)
                        except:
                            last_customer_name = 'someone'
                            user_text = user_text.replace('LAST_CUSTOMER_NAME',last_customer_name)
                    finally:
                        return user_text

    except Exception as e:
        print(e)
        number_of_purchases = 'many'
        last_customer_city = 'your city'
        last_customer_item = 'something'
        last_customer_name = 'someone'
        user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases).replace('LAST_CUSTOMER_CITY',last_customer_city).replace('LAST_CUSTOMER_ITEM',last_customer_item).replace('LAST_CUSTOMER_NAME',last_customer_name)
        return user_text
    
@campaign.route('/campaign/upload', methods=['POST','GET'])
def upload():
    if request.method == 'POST':
        site_id = request.form.get('site_id')
        if site_id == 'Open this menu':
            flash('Please select a site')
            return redirect(url_for('campaign.get_page'))
        session['site_id'] = site_id

        speech_text = request.form.get('speech_text')
        if len(speech_text) < 1:
            flash('Please enter some texts',category='error')
            return redirect(url_for('campaign.get_page'))
        
        speech_model = request.form.get('speech_model')
        if speech_model == 'Open this menu':
            flash('Please select a model',category='error')
            return redirect(url_for('campaign.get_page'))
        
        # check if the post request has the file part
        if 'speech_video' not in request.files:
            flash('Please submit a photo or video',category='error')
            return redirect(url_for('campaign.get_page'))

        speech_video = request.files['speech_video']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if speech_video.filename == '':
            flash('Please submit a photo or video', category='error')
            return redirect(url_for('campaign.get_page'))

        if speech_video and allowed_file(speech_video.filename):
            filename = secure_filename(speech_video.filename)
            speech_video.save(os.path.join('static/upload_files', filename))
            
            #Upload to GCS bucket
            user_id = session['user_id']
            access_token = session['access_token']
            bucket = gcs_client.get_bucket('deepthank-video-customer')
            blob = bucket.blob(f'{user_id}/snip{filename}')
            blob.upload_from_filename('static/upload_files/'+filename,content_type='video/mp4')

            #Save to Firestore
            db.collection(user_id).document(f'send_snippet_template_{site_id}').set({
                'user_text' : speech_text,
                'user_model' : speech_model,
                'video_url' : f'https://storage.googleapis.com/deepthank-video-customer/{user_id}/snip{filename}'
            })

            speech_text = process_user_text_snippet(user_text=speech_text,environment=environment,access_token=access_token)
            payload = {
                'user_text' : speech_text,
                'user_id' : user_id,
                'user_model' : speech_model,
                'object_id' : str(uuid.uuid1()),
                'video_url' : f'https://storage.googleapis.com/deepthank-video-customer/{user_id}/snip{filename}'
            }
            print(f"Request json is: {payload}")
            try:
                response = requests.post('https://us-central1-lively-iris-309008.cloudfunctions.net/function-1',json=payload)
                response = response.text
                print(f"Response is: {response}")
                response_dict = json.loads(response)
                if response_dict['status'] != 200:
                    flash('Lipsync Failed. Please try again.',category='error')
                    return redirect(url_for('campaign.get_page'))
                else:
                    global processed_video_url_snippet
                    processed_video_url_snippet = response_dict['processed_video_url']
                    flash('Lipsync Successful!',category='success')
                    return render_template('campaign.html',filename=processed_video_url_snippet,enable_helper_buttons=True)
            except Exception as e:
                print(f"Error is: {e}")
                flash('Lipsync Failed. Please try again.',category='error')
                return redirect(url_for('campaign.get_page')) 

@campaign.route('/campaign/retry',methods=['GET'])
def retry():
    user_id = session['user_id']
    access_token = session['access_token']
    site_id = session['site_id']
    user_text = db.collection(user_id).document(f'send_snippet_template_{site_id}').get().to_dict()['user_text']
    user_text = process_user_text_snippet(user_text=user_text,environment=environment,access_token=access_token)
    user_model = db.collection(user_id).document(f'send_snippet_template_{site_id}').get().to_dict()['user_model']
    video_url = db.collection(user_id).document(f'send_snippet_template_{site_id}').get().to_dict()['video_url']
    payload = {
        'user_text' : user_text,
        'user_id' : user_id,
        'user_model' : user_model,
        'object_id' : str(uuid.uuid1()),
        'video_url' : video_url
    }
    print(f"Request json is: {payload}")
    try:
        response = requests.post('https://us-central1-lively-iris-309008.cloudfunctions.net/function-1',json=payload)
        response = response.text
        print(f"Response is: {response}")
        response_dict = json.loads(response)
        if response_dict['status'] != 200:
            flash('Lipsync Failed. Please try again.',category='error')
            return redirect(url_for('campaign.get_page'))
        else:
            processed_video_url = response_dict['processed_video_url']
            flash('Lipsync Successful!',category='success')
            return render_template('campaign.html',filename=processed_video_url,enable_helper_buttons=True)
    except Exception as e:
        print(f"Error is: {e}")
        flash('Lipsync Failed. Please try again.',category='error')
        return redirect(url_for('campaign.get_page'))

#helper functions
def submit_snippet(processed_video_url,environment='production',access_token='EAAAEPEYWjqA0uVhsGlGuoI5RqiJbaoJu3gtCIHmbvV0lxLe0WXfnR5TKrYSxk9E',snippet_wait=3000):
    square_client = Client(environment=environment,access_token=access_token)
    sites = square_client.sites.list_sites()
    sites = sites.text
    sites_dict = json.loads(sites)
    site_id = sites_dict['sites'][0]['id']

    body = {}
    body['snippet'] = {}
    body['snippet']['content'] = '''
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-+0n0xVW2eSR5OomGNYDnhzAbDsOXxcvSN1TPprVMTNDbiYZCxYbOOl7+AMvyTG2x" crossorigin="anonymous"></link>
    <script>
    window.addEventListener('DOMContentLoaded',(event)=>{
        
        const newDiv = document.createElement("div");
        newDiv.id = "videoDiv";
        newDiv.className="modal fade";
        
        const newDialogDiv = document.createElement("div");
        newDialogDiv.className = "modal-dialog";
        newDiv.appendChild(newDialogDiv);

        const newContentDiv = document.createElement("div");
        newContentDiv.className = "modal-content";
        newContentDiv.style.background = "transparent";
        newContentDiv.style.borderRadius = "15px";
        newContentDiv.style.border = "none";
        newContentDiv.style.width = "400px";
        newContentDiv.style.height = "200px";
        newContentDiv.style.overflow = "hidden";
        newDialogDiv.appendChild(newContentDiv);

        const video = document.createElement("iframe");
        video.src = "'''+processed_video_url+'''";
        video.width = "400px";
        video.height = "200px";
        video.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
        video.style.objectFit = "cover";
        video.allowFullscreen = true;
        newContentDiv.appendChild(video);

        var modal = new bootstrap.Modal(newDiv, {
            focus: false,
        });

        setTimeout(()=>{
            modal.show();
        },'''+str(snippet_wait)+''')

    })
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js" integrity="sha384-IQsoLXl5PILFhosVNubq5LC7Qb9DXgDA9i+tQ8Zj3iwWAwPtgFTxbJ8NT4GN1R8p" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/js/bootstrap.min.js" integrity="sha384-Atwg2Pkwv9vp0ygtn1JAojH0nYbwNJLPhwyoVbhoPwBhjQPR5VtM2+xf0Uwh9KtT" crossorigin="anonymous"></script> 
    '''
    square_client.snippets.upsert_snippet(site_id=site_id,body=body)
    
@campaign.route('/campaign/submit', methods = ['GET'])
def submitted_snippet():
    submit_snippet(processed_video_url=processed_video_url_snippet)
    flash('Submitted snippet to your online store',category='success')
    return redirect(url_for('campaign.get_page'))

@campaign.route('/campaign/display/<filename>')
def display_image(filename):
    return redirect(url_for(filename))

@campaign.route('/campaign/email',methods=['GET'])
def get_email_page():
    return render_template('campaign-email.html')

#helper functions
def process_user_text_email(user_text,environment,access_token):
    square_client = Client(environment=environment,access_token=access_token)
    try: 
        payments_list = square_client.payments.list_payments()
        payments_list = payments_list.text
        payments_list_dict = json.loads(payments_list)
        try:
            number_of_purchases = str(len(payments_list_dict['payments']))
            user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases)
        except:
            number_of_purchases = 'many'
            user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases)
        finally:
            try:
                last_customer_city = str(payments_list_dict['payments'][0]['shipping_address']['locality'])
                user_text = user_text.replace('CUSTOMER_CITY',last_customer_city)
            except:
                last_customer_city = 'your city'
                user_text = user_text.replace('CUSTOMER_CITY',last_customer_city)
            finally:
                order = square_client.orders.retrieve_order(order_id=payments_list_dict['payments'][0]['order_id'])
                order = order.text
                order_dict = json.loads(order)
                try:
                    last_customer_item = order_dict['order']['line_items'][0]['name']
                    user_text = user_text.replace('CUSTOMER_ITEM',last_customer_item)
                except:
                    last_customer_item = 'your item'
                    user_text = user_text.replace('CUSTOMER_ITEM',last_customer_item)
                finally:
                    try:
                        last_customer_name = order_dict['order']['fulfillments'][0]['shipment_details']['recipient']['display_name'].split(' ')[0]
                        user_text = user_text.replace('CUSTOMER_NAME',last_customer_name)
                    except:
                        try:
                            last_customer_name = payments_list_dict['payments'][0]['shipping_address']['first_name']
                            user_text = user_text.replace('CUSTOMER_NAME',last_customer_name)
                        except:
                            last_customer_name = 'my friend'
                            user_text = user_text.replace('CUSTOMER_NAME',last_customer_name)
                    finally:
                        return user_text
    except Exception as e:
        print(e)
        number_of_purchases = 'many'
        last_customer_city = 'your city'
        last_customer_item = 'your item'
        last_customer_name = 'my friend'
        user_text = user_text.replace('NUMBER_OF_PURCHASES',number_of_purchases).replace('CUSTOMER_CITY',last_customer_city).replace('CUSTOMER_ITEM',last_customer_item).replace('CUSTOMER_NAME',last_customer_name)
        return user_text

@campaign.route('/campaign/email/upload',methods=['POST','GET'])
def upload_email():
    if request.method == 'POST':
        speech_text = request.form.get('speech_text')
        if len(speech_text) < 1:
            flash('Please enter some texts',category='error')
            return redirect(url_for('campaign.get_email_page'))
        
        speech_model = request.form.get('speech_model')
        if speech_model == 'Open this menu':
            flash('Please select a model',category='error')
            return redirect(url_for('campaign.get_email_page'))

        # check if the post request has the file part
        if 'speech_video' not in request.files:
            flash('Please submit a photo or video',category='error')
            return redirect(url_for('campaign.get_email_page'))
        
        speech_video = request.files['speech_video']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if speech_video.filename == '':
            flash('Please submit a photo or video', category='error')
            return redirect(url_for('campaign.get_email_page'))
        
        if speech_video and allowed_file(speech_video.filename):
            filename = secure_filename(speech_video.filename)
            speech_video.save(os.path.join('static/upload_files', filename))
            
            #Upload to GCS bucket
            user_id = session['user_id']
            access_token = session['access_token']
            gcs_client = gcs.Client()
            bucket = gcs_client.get_bucket('deepthank-video-customer')
            blob = bucket.blob(f'{user_id}/email{filename}')
            blob.upload_from_filename('static/upload_files/'+filename,content_type='video/mp4')

            #Save data to FireStore
            db.collection(user_id).document('send_email_template').set({
                'user_text' : speech_text,
                'user_model' : speech_model,
                'video_url' : f'https://storage.googleapis.com/deepthank-video-customer/{user_id}/email{filename}'
            })

            speech_text = process_user_text_email(user_text=speech_text,environment=environment,access_token=access_token)
            payload = {
                'user_text' : speech_text,
                'user_id' : user_id,
                'user_model' : speech_model,
                'object_id' : str(uuid.uuid1()),
                'video_url' : f'https://storage.googleapis.com/deepthank-video-customer/{user_id}/email{filename}'
            }
            print(f"Request json is: {payload}")
            try:
                response = requests.post('https://us-central1-lively-iris-309008.cloudfunctions.net/function-100',json=payload)
                response = response.text
                print(f"Response is: {response}")
                response_dict = json.loads(response)
                if response_dict['status'] != 200:
                    flash('Lipsync Failed. Please try again.',category='error')
                    return redirect(url_for('campaign.get_email_page'))
                else:
                    processed_video_url = response_dict['processed_video_url']
                    flash('Lipsync Successful!',category='success')
                    return render_template('campaign-email.html',filename=processed_video_url,enable_helper_buttons=True)
            except Exception as e:
                print(f"Error is: {e}")
                flash('Lipsync Failed. Please try again.',category='error')
                return redirect(url_for('campaign.get_email_page'))
 
@campaign.route('/campaign/email/retry',methods=['GET'])
def retry_email():
    user_id = session['user_id']
    access_token = session['access_token']
    user_text = db.collection(user_id).document('send_email_template').get().to_dict()['user_text']
    user_text = process_user_text_email(user_text=user_text,environment=environment,access_token=access_token)
    user_model = db.collection(user_id).document('send_email_template').get().to_dict()['user_model']
    video_url = db.collection(user_id).document('send_email_template').get().to_dict()['video_url']
    payload = {
        'user_text' : user_text,
        'user_id' : user_id,
        'user_model' : user_model,
        'object_id' : str(uuid.uuid1()),
        'video_url' : video_url
    }
    print(f"Request json is: {payload}")
    try:
        response = requests.post('https://us-central1-lively-iris-309008.cloudfunctions.net/function-100',json=payload)
        response = response.text
        print(f"Response is: {response}")
        response_dict = json.loads(response)
        if response_dict['status'] != 200:
            flash('Lipsync Failed. Please try again.',category='error')
            return redirect(url_for('campaign.get_email_page'))
        else:
            processed_video_url = response_dict['processed_video_url']
            flash('Lipsync Successful!',category='success')
            return render_template('campaign-email.html',filename=processed_video_url,enable_helper_buttons=True)
    except Exception as e:
        print(f"Error is: {e}")
        flash('Lipsync Failed. Please try again.',category='error')
        return redirect(url_for('campaign.get_email_page'))

@campaign.route('/settings',methods=['GET'])
def get_settings_snippet():
    site_id = ''
    sites_dict = get_user_sites()
    for site in sites_dict:
        site_id = site_id + """<option value="""+site['id']+""">"""+site['site_title']+"""</option>"""

    return render_template('settings.html',site_id=session['site_id_list_content'])

@campaign.route('/settings/upload',methods=['POST'])
def upload_snippet_settings():
    if request.method == 'POST':
        square_client = Client(environment='production',access_token=session['access_token'])
        site_id = request.form.get('site_id')
        if site_id == 'Open this menu':
            flash('Please select a site')
            return redirect(url_for('campaign.get_page'))
        session['site_id'] = site_id

        delete_snippet = square_client.snippets.delete_snippet(site_id=site_id)

        if delete_snippet.is_success:
            flash('Snippet Deleted Successfully',category='success')
        else:
            flash('Snippet Deletion Failed',category='error')
        return redirect(url_for('campaign.get_settings_snippet'))


