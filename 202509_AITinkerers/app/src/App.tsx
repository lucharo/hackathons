import { useState } from 'react'
import LandingPage from './components/LandingPage'
import OnboardingFlow from './components/OnboardingFlow'

function App() {
  const [showOnboarding, setShowOnboarding] = useState(false)

  const handleGetStarted = () => {
    setShowOnboarding(true)
  }

  const handleBackToLanding = () => {
    setShowOnboarding(false)
  }

  if (showOnboarding) {
    return <OnboardingFlow onBackToLanding={handleBackToLanding} />
  }

  return <LandingPage onGetStarted={handleGetStarted} />
}

export default App
