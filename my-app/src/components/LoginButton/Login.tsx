import { GoogleLogin } from '@react-oauth/google'

export default function LoginButton() {

  const handleSuccess = async (credentialResponse: any) => {
    const google_token = credentialResponse.credential

    try {
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
      window.location.href = '/'
    } catch (err) {
      console.error('Login error', err)
    }
  }

  const handleError = () => {
    console.error('Google Login Failed')
  }

  return <GoogleLogin onSuccess={handleSuccess} onError={handleError} />
}
