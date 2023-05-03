import whisper
from whisper.utils import format_timestamp, optional_int, optional_float, str2bool, WriteVTT, WriteSRT
import openai
import pytube
from pydub import AudioSegment
from pytube import YouTube
import smtplib
from tqdm import tqdm
import yt_dlp
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt', raise_on_error=True)

import os
import sys
import re
import shutil
import constants
import random
import string

# Set the API key
openai.api_key = constants.OPENAI_API_KEY

def convert_to_mp3(input_file, output_file, input_format):
	# Check
	print("Converting to MP3...")

	sound = AudioSegment.from_file(input_file, format=input_format)
	sound.export(output_file, format='mp3', bitrate='192k')

	# Check
	print("Done.")
	
def transcribe_audio(audio_file):

	# Check
	print("Transcribing audio...")
	
	model = whisper.load_model("small")
	result = model.transcribe(audio_file)

	# Check
	print("Done.")
	
	# Output whisper's dict
	return result

def output_files(whisper_transcript, paragraph_transcript, directory, basename):

	if whisper_transcript != None:
		# Check
		print("Creating files...")
		
		#paragraph_transcript = paragraph_transcript.replace('\u0100', '')

		# Create text file
		with open(os.path.join(directory, basename + ".txt"), "w", encoding="utf-8") as f:
			f.write(paragraph_transcript)
		print("Created transcript text file.")

		# Create VTT file
		with open(os.path.join(directory, basename + ".vtt"), "w", encoding="utf-8") as vtt:
		    WriteVTT(whisper_transcript["segments"])
		print("Created VTT file.")

		# Create SRT file
		with open(os.path.join(directory, basename + ".srt"), "w", encoding="utf-8") as srt:
		    WriteSRT(whisper_transcript["segments"])

		# Check
		print("Created SRT file.")
'''
def download_yt(url, output_path):
	# Check
	print("Downloading YouTube video...")
	
	# Create a YouTube object with the URL
	yt = pytube.YouTube(url)

	# Get the first video stream
	stream = yt.streams.first()

	# Set a temporary file name for the downloaded video
	temp_file_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
	video_title = temp_file_name + "." + stream.subtype

	# Download the stream to the specified directory with the temporary file name
	stream.download(output_path=output_path, filename=video_title)

	# Get the actual file name and path
	video_path = os.path.join(output_path, video_title)

	# Check
	print("Done.")
	
	# Return the downloaded file path
	return video_path
'''
def download_yt(url, output_path):
	# Check
	print("Downloading YouTube video...")

	# Use yt-dlp to download the video
	ydl_opts = {
		'format': 'bestaudio/best',
		'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
		'postprocessors': [{
			'key': 'FFmpegExtractAudio',
			'preferredcodec': 'mp3',
			'preferredquality': '192',
		}]
	}
	#temp_file_name = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		info_dict = ydl.extract_info(url, download=True)
		video_title = info_dict.get('title', None)
		video_path = os.path.join(output_path, video_title + '.mp3')

	# Check
	print("Done.")

	# Return the downloaded file path
	return video_path


def clean_up(save_mp3, og_file, mp3_file):

	# Check
	print("Cleaning up files.")

	if save_mp3 == False:
		os.remove(mp3_file)
		os.remove(og_file)

	elif og_file != mp3_file:
		os.remove(og_file)

	if os.path.exists("https:"):
		shutil.rmtree("https:")

	# Check
	print("Done.")

def add_paragraphs(transcript, model):
	# Check
	print("Dividing transcript into paragraphs...")
	
	result = ""

	sentences = sent_tokenize(transcript)
	i = 0
	word_count = 0

	while i < len(sentences):
		result+=sentences[i]
		words = sentences[i].split(" ")
		word_count += len(words)
		i+=1

		if word_count >= 60:
			result += "\n\n"
			word_count = 0
		else:
			result += " "

	return result

def main():

	# Ask for format
	frmt_code = int(input("""\
Which format?
0 = YouTube link
1 = .mp3
2 = .mp4
3 = .wav
4 = .mov
5 = .m4a
6 = .txt (summary only)
> """))

	formats = ['mp3', 'mp3', 'mp4', 'wav', 'mov', 'm4a', 'txt']
	frmt = formats[frmt_code]


	if frmt != 'txt':

		# Ask if should keep mp3
		save_mp3 = input("Save MP3? (y/n)\n> ")


	# Get file name/download from youtube link
	if frmt_code == 0:
		output_basename = input("Output file basename? (i.e. \"my_video\")\n> ")

		# Download youtube link 
		youtube_url = input("Enter YouTube link:\n> ")
		youtube_mp4 = download_yt(youtube_url,constants.input_dir)
		input_basename = os.path.splitext(os.path.basename(youtube_mp4))[0]

		input_file_path = os.path.join(constants.input_dir, input_basename + '.mp3')
		print(input_file_path)
	else:

		# Ask for file name
		input_basename = input("Input file basename? (i.e. \"my_video\")\n> ")
		input_file_path = os.path.join(constants.input_dir, input_basename + '.' + frmt)

		while os.path.exists(input_file_path) == False:
			input_basename = input("File doesn't exist.\nFile basename? (i.e. \"my_video\")\n> ")
			input_file_path = os.path.join(constants.input_dir, input_basename + '.' + frmt)

		if frmt != 'txt':
			output_basename = input("Output file basename? (i.e. \"my_video\")")

	if frmt != 'txt':
		# MP3 file path
		mp3 = os.path.join(constants.output_dir, input_basename + '_temp.mp3')

	if frmt == 'mp3':
		shutil.move(os.path.join(constants.input_dir, input_basename + '.mp3'), mp3)

	# Convert to mp3
	if frmt != 'mp3':
		convert_to_mp3(input_file_path, mp3, frmt)
		
	# Transcribe audio and put into object (whisper dict)
	transcript = transcribe_audio(mp3)
		
	# Divide transcript text into paragraphs
	paragraph_transcript = add_paragraphs(transcript["text"], constants.model)

	# Output files into .txt, .srt, .vtt
	output_files(transcript, paragraph_transcript, constants.output_dir, input_basename)

	# Clean up unecessary files
	clean_up(save_mp3, input_file_path, mp3)

	# Check
	print("Complete.")

if __name__ == "__main__":
	main()