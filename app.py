from chalice import Chalice
from chalice import CORSConfig
import boto3
import hashlib
import os
import praw


# initialize AWS services
polly = boto3.client('polly')
s3 = boto3.client('s3')
s3r = boto3.resource('s3')

DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "Celine")
SAMPLE_RATE = os.getenv("SAMPLE_RATE", "8000")
BUCKET_NAME = 'redditspeak'
FILE_FORMAT = os.getenv("FILE_FORMAT", "mp3")


# funtion that builds sound with Polly
def build_sound(content, subreddit, num, voice='Justin'):
    textstring = ""  # makes empty string for text
    substring = ""
    content = textstring.join(content)  # puts content into string
    subreddit = substring.join(subreddit)
    num = str(num)
    resp = polly.synthesize_speech(  # makes speech
        OutputFormat="mp3",
        Text="Here are the top" + num + "submissions for the subreddit r slash " + subreddit + ". " + content,
        TextType="text",
        VoiceId=voice
    )
    filetospeech = resp['AudioStream'].read()
    return filetospeech


def generate_hash(content):
    hasher = hashlib.md5()
    hasher.update(repr(content).encode('utf-8'))
    return hasher.hexdigest()


def redditspeech(slashr, voice, num):
    num = int(num)
    stickycounter = 0

    reddit = praw.Reddit('bot1')
    sub = reddit.subreddit(slashr)
    titles = []  # makes list
    for submission in sub.hot(limit=num):
        if submission.stickied:
            stickycounter = stickycounter + 1
    for submission in sub.hot(limit=num + stickycounter):
        if not submission.stickied:
            titles.append(str(len(titles) + 1) + ". " + submission.title)  # appends titles into list

    liststring = ". "  # divides indexes with period and space
    forspeech = liststring.join(titles)

    sound_data = build_sound(forspeech, subreddit=slashr, num=num, voice=voice)
    name = generate_hash(forspeech) + ".mp3"

    s3.put_object(Bucket=BUCKET_NAME, ACL='public-read', Body=sound_data, Key=name)

    # item = {
    #     'subreddit': slashr,
    #     'num': num,
    #     's3': "{}/{}/{}/{}".format(s3.meta.endpoint_url, BUCKET_NAME, name, forspeech)
    # }

    return 'https://s3.amazonaws.com/{}/{}'.format(BUCKET_NAME, name)


app = Chalice(app_name='redditspeak')
app.debug = True

@app.route('/subredditspeech', cors=True)
def sayit():
    subreddit = app.current_request.query_params.get('subreddit', None)
    voice = app.current_request.query_params.get('voice', None)
    numOfEntries = app.current_request.query_params.get('numOfEntries', None)
    if subreddit is None or voice is None or numOfEntries is None:
        return {'Error': 'please enter all the fields'}
    return {
        'subreddit': subreddit,
        'voice': voice,
        'numOfEntries': numOfEntries,
        'url': redditspeech(subreddit, voice, numOfEntries)
    }

# The view function above will return {"hello": "world"}
# whenever you make an HTTP GET request to '/'.
#
# Here are a few more examples:
#
# @app.route('/hello/{name}')
# def hello_name(name):
#    # '/hello/james' -> {"hello": "james"}
#    return {'hello': name}
#
# @app.route('/users', methods=['POST'])
# def create_user():
#     # This is the JSON body the user sent in their POST request.
#     user_as_json = app.current_request.json_body
#     # We'll echo the json body back to the user in a 'user' key.
#     return {'user': user_as_json}
#
# See the README documentation for more examples.
#
