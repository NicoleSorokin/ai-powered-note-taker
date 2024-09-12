'use client'
import { useState, useEffect } from 'react';
import { marked } from 'marked';
import './styles.css'; // Import the CSS file

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(''); // State for error messages
  const [processingStep, setProcessingStep] = useState(''); // State for current processing step

  // const backendBaseUrl = 'http://backend:8000'; FOR DOCKER
  const backendBaseUrl = 'http://localhost:8000';


  // test to see if the python API is working
  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${backendBaseUrl}/python`);
        const data = await res.json();
        setMessage(data.message);
      } catch {
        console.error('API Endpoint Not Working');
      }
    };

    fetchData();
  }, []);

  const startRecording = async () => {
    try {
      setIsRecording(true);
      setError(''); // Clear previous errors
      const response = await fetch(`${backendBaseUrl}/record/start/`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Error starting recording');
      }
    } catch (error) {
      setError(`Error starting recording: ${error.message}`);
    }
  };

  const fetchLatestRecording = async (filename) => {
    try {
      const response = await fetch(`${backendBaseUrl}/get-recording/?filename=${encodeURIComponent(filename)}`, {
        method: 'GET'
      });
      if (!response.ok) {
        throw new Error('Error fetching latest WAV file');
      }
      const data = await response.json();
      return data.file_base64;
    } catch (error) {
      setError(`Error fetching latest recording: ${error.message}`);
    }
  };

  const fetchTranscription = async (filename) => {
    try {
      const response = await fetch(`${backendBaseUrl}/fetch-transcription/?filename=${encodeURIComponent(filename)}`, {
        method: 'GET'
      });
      if (!response.ok) {
        throw new Error('Error fetching transcription');
      }
      const data = await response.json();
      return data.transcription_text;
    } catch (error) {
      setError(`Error fetching transcription: ${error.message}`);
    }
  };

  const stopRecording = async () => {
    try {
      setLoading(true);
      setProcessingStep('Stopping Recording...');
      setError(''); // Clear previous errors

      // Stop recording
      let response = await fetch(`${backendBaseUrl}/record/stop/`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Error stopping recording');
      }
      const { timestamp, filename } = await response.json();

      // Fetch the latest WAV file details and content
      setProcessingStep('Fetching Latest Recording...');
      const fileBase64 = await fetchLatestRecording(filename);

      // Trigger transcription
      setProcessingStep('Transcribing...');
      response = await fetch(`${backendBaseUrl}/transcribe/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          audio_content: fileBase64,
          timestamp: timestamp
        })
      });
      if (!response.ok) {
        throw new Error('Error during transcription');
      }

      // Fetch transcription text
      const transcriptionFilename = `transcription_output_${timestamp}.txt`;
      setProcessingStep('Fetching Transcription...');
      const transcriptionText = await fetchTranscription(transcriptionFilename);

      // Extract information from transcription
      setProcessingStep('Extracting Information...');
      response = await fetch(`${backendBaseUrl}/extract/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          transcription_text: transcriptionText
        })
      });
      if (!response.ok) {
        throw new Error('Error during extraction');
      }

      const extractionDetails = await response.json();

      // Process summary
      setProcessingStep('Processing Summary...');
      response = await fetch(`${backendBaseUrl}/process/`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Error during processing');
      }
      const finalNotesData = await response.json();
      const finalNotesFilename = finalNotesData.final_notes_file;

      // Get the formatted notes
      response = await fetch(`${backendBaseUrl}/output/?filename=${encodeURIComponent(finalNotesFilename)}`, {
        method: 'GET'
      });
      if (!response.ok) {
        throw new Error('Error fetching notes');
      }
      const notesData = await response.json();
      setNotes(notesData.final_notes || 'No notes available');

    } catch (error) {
      setError(`Error processing recording: ${error.message}`);
    } finally {
      setIsRecording(false);
      setLoading(false);
      setProcessingStep(''); // Clear processing step when done
    }
  };

  // Convert Markdown to HTML
  const getMarkdownText = (markdown) => {
    const renderer = new marked.Renderer();
    renderer.link = (href, title, text) => {
      return `<a href="${href}" title="${title}" target="_blank" rel="noopener noreferrer">${text}</a>`;
    };
  
    const rawMarkup = marked(markdown, { renderer });
    return { __html: rawMarkup };
  };

  return (
    <div>
      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <h1>AI-Powered Note-Taker</h1>
        {error && <div style={{ color: 'red' }}>{error}</div>} {/* Display error messages */}
        {!isRecording ? (
          <button onClick={startRecording} disabled={loading}>
            {loading ? 'Loading...' : 'Start Recording'}
          </button>
        ) : (
          <button onClick={stopRecording} disabled={loading}>
            {loading ? processingStep || 'Processing...' : 'Stop Recording'}
          </button>
        )}
      </div>
      {notes && (
        <div>
          <h2>Notes:</h2>
          <div dangerouslySetInnerHTML={getMarkdownText(notes)} />
        </div>
      )}
    </div>
  );
}
