import { useNavigate } from 'react-router-dom'

export default function SignOutButton() {
  const navigate = useNavigate()

  const handleSignOut = async () => {
    const session_token = localStorage.getItem('session_token')

    if (session_token) {
      await fetch(`${import.meta.env.VITE_FLASK_URL}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_token }),
      })
      localStorage.removeItem('session_token')
    }

    navigate('/login')
  }

  return <button onClick={handleSignOut}>Sign Out</button>
}
