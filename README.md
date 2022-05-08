# DeepThankSquareHackathon
Submission for Square Unboxed Hackathon 2021: https://devpost.com/software/deepthank

# Inspiration
Customer impression is an important part of any businesses. Independent shops have longed for a way to create a good impression on customers and make customers remember where they buy from. Better impressions from customers will lead to better rate of customer acquisitions. DeepThank presents a solution to this by combining real-time personalization powered by AI and Square API with memes and some creative humour from shop owners!

This is the FIRST app of its kind that has not been seen in any other major e-commerce app platforms such as Shopify, WooCommerce, etc and I am delighted to bring this app to Square first!

Here is the link that the thesis of this app is based on, take a look at the enthusiastic responses from sellers: https://www.reddit.com/r/shopify/comments/lh80az/sending_thank_you_videos_to_increase_returning

# What it does
DeepThank currently has 2 features:

Upserting real-time welcome video snippets to Square Online websites.

Sending customers personalized thank-you videos right after customers made their purchases.

# How we built it
For the backend: I used heavily Square Payments, Orders and Customers API along with Square Snippet, Sites and Oauth API. The backend is mainly Flask and Nginx deployed on Google Cloud Run and Google Compute Engine servers along with Node.js on Google Cloud Functions with Google Cloud Firestore for real-time updates and Google Cloud Storage for images/videos storage.

For the ML models: There are 4 different ML models used altogether in this app. The ML models are trained on around 40 minutes of speech data (of course, the models will even get better if it was fed more data):

_ The first one is based on Tacotron2 architecture to generate voice spectrogram' i.e voice DNA, from the dataset

_ The second one is built on an architecture called MelGAN which uses a Deep Learning Technique called Generative Adversarial Networks (GANs) that generate waveform from the voice spectrogram from Tacotron2. MelGAN does not originally come with Tacotron2 so I have to build my own implementation to plug it into Tacotron2.

_ The third one is also built on a GAN architecture called LipGAN to generate lip movement animation that syncs with the waveform from MelGAN and then dub the waveform to the animation using ffmpeg for lipsync effect. LipGAN does not naturally go along well with synthetic robotic-sounding voice that usually comes from Tacotron2+MelGAN so I also have to build my implementation with some twists of this architecture.

_The fourth one is a custom-built face recognition model that used in conjunction with LipGAN. I intended to use Google Cloud Vision APIs for this task but realized it doesn't recognize well the lower part of the face necessary for lipsync so I have to build a model from scratch.

For the frontend: Simple web app with vanilla Javascript and Bootstrap 5.

# Challenges we ran into
My original idea is to produce the video right after the customer made the purchase and show the video on the thank you page for an even more real-time feel. However this is not feasible (yet)! Because Square Snippet doesn't allow for this so I had to pivot to sending email to the customer. It would be great if Square can add more real time event notification to Snippet API in the future!!!

Collecting and cleaning and labelling and training speech data took a lot of time. Furthermore building and implementing ML models are not easy. Usually in current Text-To-Speech engines people mainly use the Tacotron2 + Wavenet/Waveglow combo but for this hackathon I used Tacotron2 + MelGAN because this combo is more lightweight and more economical (also because I tried to challenge myself too).

A problem that I am still trying but have not solved yet is to control the tempo and intonation and pauses between the sentences. Sometimes the wave file ended suddenly before finished. A good possible solution is to build a SSML engine (Speech Synthesis Markup Language, which is basically HTML but for text-to-speech) but this would be out of scope of this hackathon duration.

For some reasons, Python dependencies necessary for the ML models tend to clash with each other so I have to build Docker image for each of the model to better manage their environments and it turned out that building containers that can integrate with Pytorch and GPUs and CUDA platform was much harder than I expected! It took me 3 full days to figure this out without breaking anything.

I planned for a more polished web app in terms of front-end and full-fledged side features like Dashboard, History, Settings, etc but I was unable to finish them on time. I seriously overestimated myself when thinking that I could do all of them alone.

Accomplishments that we're proud of
This is actually my first hackathon ever so I am proud that I, at least, managed to finish it!

# What we learned
I learned a great deal about e-commerce and fintech through this hackathon. I knew next to nothing about these areas before this hackathon and Square solutions showed me what real business solutions should look like. All the Square hardware and software products and APIs are well thought-out and stem from real pain points of sellers and buyers.

I also, unexpectedly, learned about DevOps through a fintech hackathon! Because this time I have to build a production-grade software with GPU and CUDA/CuDNN, I have to configure manually my own servers and load balancers and networking. Before this, I almost always use some serverless solutions: write the codes and sprinkle some YAML on them and call it a day. It was a great learning experience.

# What's next for DeepThank
There are many plans for DeepThank:

The most important plan is to allow shop owners to record their own voices and send their voice data to DeepThank to generate their voice model. This will allow shop owners to get close to customers without even trying!

Continue to optimize the current voice models and lipsync models and build new voice models with different voices from fictional characters. I will build a SSML engine to make the voice model more accurate in terms of expression, intonation and pause. The current voice models still lack in this aspect and needs to be worked on further.

Build a new feature to send automatic email to customers on their birthday and holidays.

Integrate with APIs like Facebook API, Instagram API to better target what customers like.

And of course, release on Square App Marketplace if possible!

This is only Day One for DeepThank!!!
