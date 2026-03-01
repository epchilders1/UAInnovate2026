import './LoginPage.css';
import LoginButton from '../../components/LoginButton/Login';
import Threads from './Threads';

export default function LoginPage(){
    return(
        <div className="login-page-container">
                <Threads
                    amplitude={1}
                    distance={0}
                    enableMouseInteraction={false}
                />
            <div className="login-content">
                <div className="login-card">
                    <p className="login-card__eyebrow">
                        <span className="login-card__dot" />
                        STARK INDUSTRIES — CLEARANCE REQUIRED
                        <span className="login-card__dot" />
                    </p>
                    <h1 className="login-card__wordmark">JFX</h1>
                    <p className="login-card__sub">Jarvis Forecasting Expert</p>
                    <div className="login-card__divider" />
                    <LoginButton/>
                    <p className="login-card__footer">Unauthorized access is monitored and prosecuted.</p>
                </div>
            </div>
        </div>
    );
}
