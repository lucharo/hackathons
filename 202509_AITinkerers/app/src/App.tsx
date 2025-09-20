import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
      <div className="max-w-4xl mx-auto p-8 text-center">
        <div className="flex justify-center space-x-8 mb-8">
          <a href="https://vite.dev" target="_blank" className="block">
            <img 
              src={viteLogo} 
              className="h-24 p-6 transition-all duration-300 hover:drop-shadow-[0_0_2em_#646cffaa] will-change-transform" 
              alt="Vite logo" 
            />
          </a>
          <a href="https://react.dev" target="_blank" className="block">
            <img 
              src={reactLogo} 
              className="h-24 p-6 transition-all duration-300 hover:drop-shadow-[0_0_2em_#61dafbaa] will-change-transform animate-spin-slow" 
              alt="React logo" 
            />
          </a>
        </div>
        
        <h1 className="text-5xl font-bold mb-8 text-gray-900 dark:text-white leading-tight">
          Vite + React
        </h1>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <button 
            onClick={() => setCount((count) => count + 1)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 border border-transparent hover:border-blue-500 focus:outline-none focus:ring-4 focus:ring-blue-300 dark:focus:ring-blue-800"
          >
            count is {count}
          </button>
          <p className="mt-4 text-gray-600 dark:text-gray-300">
            Edit <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-sm font-mono">src/App.tsx</code> and save to test HMR
          </p>
        </div>
        
        <p className="text-gray-500 dark:text-gray-400">
          Click on the Vite and React logos to learn more
        </p>
      </div>
    </div>
  )
}

export default App
