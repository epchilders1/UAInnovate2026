import { GoogleLogin } from '@react-oauth/google'
import { useNavigate } from 'react-router-dom'

export default function LoginButton() {
  const navigate = useNavigate()

  const handleSuccess = async (credentialResponse: any) => {
    const google_token = credentialResponse.credential

    const res = await fetch(`${import.meta.env.VITE_FLASK_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ google_token }),
    })

    if (!res.ok) {
      console.error('Login failed', await res.text())
      return
    }

    const { session_token } = await res.json()
    localStorage.setItem('session_token', session_token)
    navigate('/')
  }

  const handleError = () => {
    console.error('Google Login Failed')
  }

  return <GoogleLogin onSuccess={handleSuccess} onError={handleError} />
}
