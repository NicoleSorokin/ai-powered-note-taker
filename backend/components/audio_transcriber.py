import openai
from io import BytesIO
from pydub import AudioSegment
# your_file.py in /other_directory

from prompt_eng.prompt_manager import PromptManager

pm = PromptManager()
transcription_prompt = pm.get_prompt("transcription")

class AudioTranscriber:
    def __init__(self, api_key, chunk_length=60 * 1000):
        openai.api_key = api_key
        self.chunk_length = chunk_length

    def transcribe_audio(self, audio_io):
        # Ensure the stream is at the beginning
        audio_io.seek(0)
        
        # Convert the BytesIO stream to a file-like object
        file = {'file': ('audio.wav', audio_io, 'audio/wav')}
        
        # Make the request to OpenAI API
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            **file, 
            prompt=transcription_prompt
        )
        
        return transcription.text

    # if audio is too large, split it into chunks
    def split_audio(self, audio_io):
        audio = AudioSegment.from_file(audio_io, format="wav")
        file_size = audio_io.getbuffer().nbytes

        if file_size < 25 * 1024 * 1024:  # 25MB
            return [audio_io]
        
        chunks = []
        duration_ms = len(audio)
        chunk_start = 0
        
        while chunk_start < duration_ms:
            chunk_end = min(chunk_start + self.chunk_length, duration_ms)
            chunk = audio[chunk_start:chunk_end]
            chunk_io = BytesIO()
            chunk.export(chunk_io, format="wav")
            chunk_io.seek(0)
            chunks.append(chunk_io)
            chunk_start = chunk_end

        return chunks
    
    def get_audio_duration(self, audio_io):
        audio = AudioSegment.from_file(audio_io, format="wav")
        duration_ms = len(audio)
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        return minutes, seconds

    def process_audio(self, audio_io):
        # Get audio duration
        minutes, seconds = self.get_audio_duration(audio_io)
        
        # Split the audio into chunks if necessary
        audio_chunks = self.split_audio(audio_io)
        full_transcription = ""

        # Transcribe each chunk and concatenate the results
        for chunk_io in audio_chunks:
            transcription = self.transcribe_audio(chunk_io)
            full_transcription += transcription + "\n"
        
        return minutes, seconds, full_transcription.strip()
