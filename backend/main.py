from fastapi import FastAPI, Form, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from http.client import HTTPException
from components.audio_recorder import AudioRecorder
from components.audio_transcriber import AudioTranscriber
from components.extraction import Extraction
from components.processing import Processing
from dotenv import load_dotenv
from datetime import datetime
from google.cloud import storage
import os
import io
import base64

# Load environment variables from .env file
load_dotenv()

# initialize FastAPI app
app = FastAPI()

# Configure CORS
origins = ["*"]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define global variables
audio_duration = {"minutes": 0, "seconds": 0}
extraction_details = {
            'meeting_title': None, 
            'meeting_type': None, 
            'minutes': 0, 
            'seconds': 0, 
            'general_extraction': None
        }
summary = ''

# Load API key from environment variable
api_key = os.getenv("OPEN_API_KEY")  

# create instances of required classes
recorder = AudioRecorder()
transcriber = AudioTranscriber(api_key=api_key)
extractor = Extraction(api_key=api_key)

# hello world to check if backedn is up and running
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/python")
async def root_py():
    return {"message": "Hello from fastAPI backend"}

# start recording 
@app.post("/record/start/")
async def start_recording():
    recorder.start_recording()
    return {"message": "Recording started"}

# stop recording and upload to local folder
@app.post("/record/stop/")
async def stop_recording():
    try:
        timestamp, filename, wav_io = recorder.stop_recording()

        # upload wav_io contents in file named filename to ../assets/audio_output folder
        # Define the path where the file will be saved
        output_folder = "assets/audio_output"
        file_path = os.path.join(output_folder, filename)

        # Create the folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Write the wav_io contents to the file
        with open(file_path, "wb") as f:
            f.write(wav_io.getbuffer())


        return {"timestamp": timestamp, "filename": filename}
    
    except Exception as e:
        print(f"Failed to upload to GCS: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
# retreive the latest recording from ../assets/audio_output folder
@app.get("/get-recording/")
async def get_recording(filename: str = Query(...)):
    folder_path = os.path.join(os.path.dirname(__file__), "../assets/audio_output")

    # Ensure the folder exists
    if not os.path.exists(folder_path):
        raise HTTPException(status_code=404, detail="Audio output folder not found")

    # Get the path of the specified file in the folder
    file_path = os.path.join(folder_path, filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Recording file not found")

    # Read the file as bytes
    try:
        with open(file_path, "rb") as audio_file:
            file_bytes = audio_file.read()

        # Convert the file bytes to base64
        file_base64 = base64.b64encode(file_bytes).decode('utf-8')

        return {"file_base64": file_base64}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {e}")

# transcribe the latest recording and save to ./assets/transcription_audio folder
@app.post("/transcribe/")
async def transcribe_audio(
    audio_content: str = Form(...),
    timestamp: str = Form(...)
):
    try:
        global audio_duration
        global extraction_details

        # Decode the base64-encoded audio content
        audio_bytes = base64.b64decode(audio_content)

        # Create a BytesIO object to pass to the transcriber
        audio_io = io.BytesIO(audio_bytes)

        # Transcribe the audio using the transcriber (assuming it returns minutes, seconds, and text)
        minutes, seconds, transcription_text = transcriber.process_audio(audio_io)
        audio_duration = {"minutes": minutes, "seconds": seconds}
        extraction_details["minutes"] = minutes
        extraction_details["seconds"] = seconds

        # Generate a transcription file name using the timestamp
        transcription_filename = f"transcription_output_{timestamp}.txt"

        # Define the folder to save the transcription
        transcription_folder = os.path.join(os.path.dirname(__file__), "../assets/transcription_audio")

        # Ensure the folder exists, create it if not
        os.makedirs(transcription_folder, exist_ok=True)

        # Full path to the transcription file
        transcription_filepath = os.path.join(transcription_folder, transcription_filename)

        # Save the transcription text to a file
        with open(transcription_filepath, "w") as transcription_file:
            transcription_file.write(transcription_text)

        return {
            "transcription_file_name": transcription_filename,
            "duration": {"minutes": minutes, "seconds": seconds}
        }

    except Exception as e:
        print(f"Failed to transcribe audio: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {e}")
    
# fetch the transcription file from ../assets/transcription_audio folder
@app.get("/fetch-transcription/")
async def fetch_transcription(filename: str = Query(...)):
    try:
        # Define the path to the transcription folder
        transcription_folder = os.path.join(os.path.dirname(__file__), "../assets/transcription_audio")

        # Construct the full path to the file
        transcription_filepath = os.path.join(transcription_folder, filename)

        # Check if the file exists
        if not os.path.exists(transcription_filepath):
            raise HTTPException(status_code=404, detail="Transcription file not found")

        # Read the transcription file content as a string
        with open(transcription_filepath, "r") as transcription_file:
            transcription_text = transcription_file.read()

        return {"transcription_text": transcription_text}

    except Exception as e:
        print(f"Failed to get transcription file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcription: {e}")

# extract information from the transcription
@app.post("/extract/")
async def extract_information(body: dict = Body(...)):
    try : 
        global audio_duration
        global extraction_details

        transcriptionText = body.get("transcription_text")
        if not transcriptionText:
            raise HTTPException(status_code=404, detail="No transcription files found")

        # Process the transcription to extract information
        extraction_details = extractor.process(transcriptionText, audio_duration["minutes"], audio_duration["seconds"])

        return {"extraction": extraction_details}
    
    except Exception as e:
        print(f"Failed to extract information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# process the information and create a concise summary and upload to ../assets/notes folder
@app.post("/process/")
async def process_summary():
    try:
        global extraction_details
        global summary

        # Initialize the processor with API key and extraction details
        processor = Processing(api_key=api_key, details=extraction_details)

        # Create a concise summary
        summary = processor.process()

        # Extract meeting title and current date
        meeting_title = extraction_details.get('meeting_title', 'Untitled_Meeting')
        meeting_date = datetime.now().strftime('%Y-%m-%d')

        # Clean up the file name by replacing spaces and removing invalid characters
        filtered_title = meeting_title.replace(' ', '_').replace('"', '').replace("'", "")
        file_name = f"{filtered_title}_{meeting_date}.md"

        # Define the path to the notes folder
        notes_folder = os.path.join(os.path.dirname(__file__), "../assets/notes")

        # Ensure the folder exists, create it if it doesn't
        os.makedirs(notes_folder, exist_ok=True)

        # Full path to the final notes file
        notes_file_path = os.path.join(notes_folder, file_name)

        # Write the summary to the markdown file
        with open(notes_file_path, "w") as notes_file:
            notes_file.write(summary)

        return {"final_notes_file": file_name}

    except Exception as e:
        print(f"Failed to process summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process summary: {e}")

# fetch the final notes file from ../assets/notes folder and send to frontend
@app.get("/output/")
async def get_output_notes(filename: str = Query(...)):
    try:
        # Define the path to the notes folder
        notes_folder = os.path.join(os.path.dirname(__file__), "../assets/notes")

        # Construct the full path to the file
        file_path = os.path.join(notes_folder, filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Final notes file not found")

        # Read the final notes file content as a string
        with open(file_path, "r") as file:
            final_notes = file.read()

        # Return the final notes content
        return {"final_notes": final_notes}

    except Exception as e:
        print(f"Failed to get final notes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch final notes: {e}")

@app.on_event("shutdown")
def shutdown_event():
    recorder.terminate()