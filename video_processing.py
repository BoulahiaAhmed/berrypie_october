import streamlit as st
import moviepy.editor as mp
import os

import cv2
import base64
import json

from groq import Groq
from dotenv import load_dotenv


# Load environment variables from a .env file

#GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize the Groq client
client = Groq(api_key=GROQ_API_KEY)


def extract_audio_from_video(video_path, output_audio_path):
    """Extracts audio from the video file and saves it as MP3."""
    # Load the video file
    video = mp.VideoFileClip(video_path)
    # Create a temporary path for the WAV file
    audio_path = output_audio_path.replace(".mp3", ".wav")
    # Extract and save the audio as a WAV file
    video.audio.write_audiofile(audio_path)
    return audio_path


def transcribe_audio_with_whisper(audio_path):
    """Transcribes the audio using the specified Whisper model."""
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(audio_path, audio_file.read()),
            model="whisper-large-v3",
            prompt="Specify context or spelling",
            response_format="json",
            temperature=0.0
        )
        return transcription.text


def frame_to_base64(frame):
    """Convert a video frame (OpenCV image) to a base64-encoded string."""
    try:
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        print(f"Error converting frame to base64: {e}")
        return None


def process_frame(base64_image):
    """Processes the base64 image by sending it to the Groq API for text extraction."""
    text_prompt = """
    Your task is to extract the text from the provided image, focusing on any small disclaimers or warnings written in small size.
    Ensure that you provide the extracted text in JSON format, using the following structure:
    {
        "image_content": ""
    }

    If no text is presented in the image return this JSON format: 
    {
        "image_content": "No text presented in the image"
    }
    """

    client = Groq(api_key=GROQ_API_KEY)
    try:
        # Send the image for processing to the Groq API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
            stream=False,
            stop=None,
        )
        
        # Parse the result
        result = json.loads(chat_completion.choices[0].message.content)
        return result["image_content"]
    
    except Exception as e:
        print(f"Error processing frame: {e}")
        return None


def extract_and_process_frames(video_path, interval_seconds=5):
    """Extract frames from the video and process each frame for text extraction."""
    # Open the video file
    video = cv2.VideoCapture(video_path)
    
    # Get the frames per second (fps) of the video
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    success, frame = video.read()

    # List to store all extracted texts
    extracted_texts = []

    while success:
        # Calculate the current timestamp in seconds
        current_time_sec = frame_count / fps
        
        # Extract frame every `interval_seconds`
        if current_time_sec % interval_seconds == 0:
            print(f"Processing frame at {int(current_time_sec)} seconds")
            
            # Convert the frame to base64
            base64_image = frame_to_base64(frame)
            
            if base64_image:
                # Process the base64 image to extract text
                extracted_text = process_frame(base64_image)
                if extracted_text:
                    print(f"Text from frame: {extracted_text}")
                    extracted_texts.append(extracted_text)  # Add the extracted text to the list
            else:
                print("no base64_image")
            
        # Read the next frame
        success, frame = video.read()
        frame_count += 1

    # Release the video capture object
    video.release()

    # Return the list of all extracted texts
    return extracted_texts


def check_and_extract_disclaimer(extracted_texts):
    system_message = """
        You are tasked with reviewing a list of texts to identify any disclaimer or warning messages.
        Multiple texts in the list may be similar. 
        Your goal is to check if a disclaimer or warning is present.
        If a disclaimer is found, extract a single best version and return the following JSON format:
        {
            "disclaimer_is_exist": "",
            "disclaimer_text": "Extracted disclaimer text here"
        }
        
        If no disclaimer is found in the list, return the following JSON format with disclaimer_is_exist set to false:
        {
            "disclaimer_is_exist": false,
            "disclaimer_text": ""
        }
        """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"{system_message}"
                },
                {
                    "role": "user",
                    "content": f"This is the list that contains the extracted text: {extracted_texts}",
                }
            ],
            model="llama-3.2-90b-text-preview",
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=500,
            stream=False,
            stop=None,
        )
        print(chat_completion.choices[0].message.content)
        result = json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"Error processing the list: {e}")

    return result


def video_media_processing(video_path):
    extracted_texts = extract_and_process_frames(video_path)
    result = check_and_extract_disclaimer(extracted_texts)
    checker_flag = result['disclaimer_is_exist']
    disclaimer_text = result['disclaimer_text']
    print(f"---\n Disclaimer exist : {checker_flag},\n disclaimer text: {disclaimer_text}")
    return result
