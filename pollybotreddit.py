#!/usr/bin/python
import boto3
import hashlib
import json
import os
import praw
import tempfile
import random

#initialize AWS services
polly = boto3.client('polly') 
s3 = boto3.client('s3')
s3r = boto3.resource('s3')

DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "Celine")
SAMPLE_RATE = os.getenv("SAMPLE_RATE", "8000")
BUCKET_NAME = os.getenv("BUCKET_NAME", "pollybotreddit")
FILE_FORMAT = os.getenv("FILE_FORMAT", "mp3")

#funtion that builds sound with Polly
def build_sound(content, subreddit, num, voice = 'Justin', SampleRate = SAMPLE_RATE): 
	textstring = ""    #makes empty string for text
	substring = ""
	content = textstring.join(content)    #puts content into string
	subreddit = substring.join(subreddit)
	num = str(num)
	resp = polly.synthesize_speech(    #makes speech
			OutputFormat = "mp3",
			Text = "Here are the top" + num + "submissions for the subreddit r slash " + subreddit + ". " + content,
			TextType = "text",
			VoiceId = voice
		)
	filetospeech = resp['AudioStream'].read() 
	return filetospeech 

def generate_hash(content):
	hasher = hashlib.md5()
	hasher.update(repr(content).encode('utf-8'))
	return hasher.hexdigest()	

def lambda_handler(event, num, content):
	slashr = event.get('subreddit') 
	voice = event.get('voice', 'personVoice')
	num = num 
	stickycounter = 0

	reddit = praw.Reddit('bot1')
	sub = reddit.subreddit(slashr)
	titles = []    #makes list
	for submission in sub.hot(limit=num):
		if submission.stickied:
			stickycounter = stickycounter + 1
	for submission in sub.hot(limit=num + stickycounter):
		if not submission.stickied:
			titles.append( str(len(titles)+ 1) + ". " + submission.title) #appends titles into list

	liststring = ". " #divides indexes with period and space
	forspeech = liststring.join(titles) 

	sound_data = build_sound(forspeech, subreddit=slashr , num=num, voice=voice) 
	name = generate_hash(forspeech) + ".mp3"

	s3.put_object(Bucket=BUCKET_NAME, ACL='public-read', Body=sound_data, Key=name)

	item = {
		'subreddit': slashr,
		'num': num,
		's3': "{}/{}/{}/{}".format(s3.meta.endpoint_url, BUCKET_NAME, name, forspeech)
		}

	print (item)

lambda_handler({'subreddit':"movies",'voice':'Brian'},4, None)
