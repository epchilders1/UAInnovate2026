import { useJarvis } from '../../context/JarvisContext'
import { useLoading } from '../../context/LoadingContext'
import './JarvisOverlay.css'

function PulseDots() {
    return (
        <div className="pulse-dots">
            <span className="pulse-dot pulse-dot--1" />
            <span className="pulse-dot pulse-dot--2" />
            <span className="pulse-dot pulse-dot--3" />
            <span className="pulse-dot pulse-dot--4" />
        </div>
    );
}

export default function JarvisOverlay(){
    const { askingPrompt, transcript } = useJarvis();
    const { loading } = useLoading();
    if (!askingPrompt) return null;
    return(
        <div className="jarvis-overlay">
            <div className="jarvis-hud">
                <PulseDots />
                <div className="jarvis-hud__text">
                    {loading
                        ? <span className="jarvis-hud__status">Just a moment…</span>
                        : <span className="jarvis-hud__transcript">{transcript || 'Listening…'}</span>
                    }
                </div>
            </div>
        </div>
    )
}
