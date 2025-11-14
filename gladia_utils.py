import os 
import requests
import mimetypes
import time
import streamlit as st
GLADIA_UPLOAD_URL = "https://api.gladia.io/v2/upload"
GLADIA_TRANSCRIPTION_URL = "https://api.gladia.io/v2/pre-recorded"
TIME_INTERVAL = 2
TOTAL_REQUESTS = 10
os.environ["GLADIA_API_KEY"] = st.secrets["GLADIA_API_KEY"]

def upload_file_to_gladia(file_path:str,api_key:str=os.environ["GLADIA_API_KEY"])-> dict:
    headers = {"x-gladia-key":api_key}
    with open(file_path,'rb') as audio_file:
        mime = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
        files = {"audio":(os.path.basename(file_path),audio_file,mime)}
    try:
        response = requests.post(GLADIA_UPLOAD_URL,files=files,headers=headers)
        api_response_url = response.json()["audio_url"]
        return {"audio_url": api_response_url}
    except Exception as e:
        print(f"error uploading file to gladia: {e}")
        return {"audio_url" : None}
def transcribe_audio(audio_url:str,api_key:str=os.environ["GLADIA_API_KEY"],**options)-> dict:
    headers = {"x-gladia-key":api_key,"Content-type":"application/json"}
    data = {"audio_url":audio_url}
    data.update(options)
    try:
        response = requests.post(GLADIA_TRANSCRIPTION_URL,header=headers,json=data)
        data_id=response.json()["id"]
        return {"transcription_id":data_id }
    except Exception as e:
        print(f"error transcribing audio:{e}")
        return {"transcription_id" : None}
def get_transcription_result(transcription_id:str,api_key:str=os.environ["GLADIA_API_KEY"])->dict:
    url=f"{GLADIA_TRANSCRIPTION_URL}/{transcription_id}"
    headers = {"x-gladia-key":api_key,"Content-type":"application/json"}
    try:
        response = requests.get(url,headers=headers)
        transcript_response=response.json()
        if transcript_response["status"]=="done":
            return {"transcript": transcript_response["result"]["transcription"]["utterances"],"status":"done"}
        elif transcript_response["status"]=="processing":
            return {"transcript": None, "status":"processing"}
        elif transcript_response["status"]=="queued":
            return {"transcript": None, "status":"queued"}
    except Exception as e:
        print(f"Error getting transcription result: {e}")
        return {
            "transcript": None,
            "status": "failed",
        }
def poll_transcription(transcription_id: str) -> dict:
    request_count = 0
    while True:
        request_count += 1
        result = get_transcription_result(transcription_id)
        if result["status"] == "done":
            return result
        elif result["status"] == "processing":
            time.sleep(TIME_INTERVAL)
        elif result["status"] == "queued":
            time.sleep(TIME_INTERVAL)
        else:
            return result
        # if polling persists, break the loop
        if request_count == TOTAL_REQUESTS:
            return result