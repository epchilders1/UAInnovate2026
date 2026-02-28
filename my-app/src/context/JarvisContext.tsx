import { createContext, useContext, useEffect, useState } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { useLoading } from './LoadingContext';

const TRIGGER_STRINGS = ['hey jarvis', 'ok jarvis', 'okay jarvis'];

async function speakText(text: string) {
    const response = await fetch(
        `https://api.elevenlabs.io/v1/text-to-speech/${import.meta.env.VITE_ELEVENLABS_VOICE_ID}`,
        {
            method: 'POST',
            headers: {
                'xi-api-key': import.meta.env.VITE_ELEVENLABS_API_KEY,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text, model_id: 'eleven_turbo_v2' }),
        }
    );
    if (!response.ok) {
        console.error('ElevenLabs error:', await response.text());
        return;
    }
    const audioBlob = await response.blob();
    const audio = new Audio(URL.createObjectURL(audioBlob));
    audio.play();
}

interface JarvisContextType {
    askingPrompt: boolean;
    transcript: string;
}

const JarvisContext = createContext<JarvisContextType | null>(null);

export function JarvisProvider({ children }: { children: React.ReactNode }) {
    const { transcript, resetTranscript } = useSpeechRecognition();
    const { setLoading } = useLoading();
    const [askingPrompt, setAskingPrompt] = useState(false);

    useEffect(() => {
        SpeechRecognition.startListening({ continuous: true });
        return () => { SpeechRecognition.stopListening(); };
    }, []);

    useEffect(() => {
        const interval = setInterval(() => {
            if (!askingPrompt) resetTranscript();
        }, 10000);
        return () => clearInterval(interval);
    }, [askingPrompt]);

    useEffect(() => {
        if (TRIGGER_STRINGS.some((keyword) => transcript.toLowerCase().includes(keyword))) {
            resetTranscript();
            setAskingPrompt(true);
        }
    }, [transcript]);

    useEffect(() => {
        if (!askingPrompt || !transcript) return;
        const timer = setTimeout(async () => {
            console.log('Sending to API:', { prompt: transcript });
            const response = await fetch(`${import.meta.env.VITE_FLASK_URL}/ask_jarvis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: transcript }),
            });
            const data = await response.json();
            console.log('Response:', data);
            if (data?.response) await speakText(data.response);
            setAskingPrompt(false);
            setLoading(false);
            resetTranscript();
        }, 2000);
        return () => clearTimeout(timer);
    }, [transcript, askingPrompt]);

    useEffect(() => {
        if (transcript) console.log(transcript);
    }, [transcript]);

    return (
        <JarvisContext.Provider value={{ askingPrompt, transcript }}>
            {children}
        </JarvisContext.Provider>
    );
}

export function useJarvis() {
    const ctx = useContext(JarvisContext);
    if (!ctx) throw new Error('useJarvis must be used within a JarvisProvider');
    return ctx;
}