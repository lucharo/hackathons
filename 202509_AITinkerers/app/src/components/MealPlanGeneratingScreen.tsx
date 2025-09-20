import { useState, useEffect } from 'react';

const loadingMessages = [
  "Analyzing your preferences...",
  "Crafting personalized meals...",
  "Finding the perfect recipes..."
];

export default function MealPlanGeneratingScreen() {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

  useEffect(() => {
    const messageInterval = setInterval(() => {
      setCurrentMessageIndex((prev) => (prev + 1) % loadingMessages.length);
    }, 1500); // Change message every 1.5 seconds

    return () => {
      clearInterval(messageInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-6">
      <div className="text-center max-w-2xl mx-auto">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8">
          DishGenius is Generating Your Meal Plan
        </h1>
        
        <div className="mb-8 flex justify-center">
          <div className="relative w-16 h-16">
            <div className="absolute top-0 left-0 w-4 h-4 bg-green-500 rounded-full animate-ping"></div>
            <div className="absolute top-0 right-0 w-4 h-4 bg-blue-500 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
            <div className="absolute bottom-0 left-0 w-4 h-4 bg-purple-500 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
            <div className="absolute bottom-0 right-0 w-4 h-4 bg-orange-500 rounded-full animate-ping" style={{ animationDelay: '0.6s' }}></div>
          </div>
        </div>
        
        <p className="text-xl text-gray-600 mb-4 h-8 flex items-center justify-center transition-all duration-300">
          {loadingMessages[currentMessageIndex]}
        </p>
        
        <div className="text-sm text-gray-500">
          This usually takes just a few moments...
        </div>
      </div>
    </div>
  );
}
