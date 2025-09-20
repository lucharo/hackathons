import { useState } from 'react';

interface GoalsScreenProps {
  onSubmit: (selectedGoals: string[]) => void;
  onBack: () => void;
  initialSelected: string[];
}

const goals = [
  'Save money',
  'Waste less food',
  'Discover New Recipes',
  'Save time',
  'Eat healthy',
  'Easier Meal planning'
];

export default function GoalsScreen({ onSubmit, onBack, initialSelected }: GoalsScreenProps) {
  const [selectedGoals, setSelectedGoals] = useState<string[]>(initialSelected);

  const toggleGoal = (goal: string) => {
    setSelectedGoals(prev => 
      prev.includes(goal) 
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  const handleContinue = () => {
    onSubmit(selectedGoals);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex-1 max-w-2xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            What are your goals with HelloFresh?
          </h1>
          <p className="text-lg text-gray-600 max-w-lg mx-auto">
            Let us know what's important to you.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 mb-12">
          {goals.map((goal) => (
            <button
              key={goal}
              onClick={() => toggleGoal(goal)}
              className={`p-6 rounded-xl text-left transition-all duration-200 font-medium text-lg ${
                selectedGoals.includes(goal)
                  ? 'bg-green-500 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {goal}
            </button>
          ))}
        </div>

        <div className="flex justify-center gap-4">
          <button
            onClick={onBack}
            className="bg-white border-2 border-gray-300 text-gray-700 px-12 py-4 rounded-xl text-lg font-medium hover:border-gray-400 transition-colors duration-200"
          >
            Back
          </button>
          <button
            onClick={handleContinue}
            className="bg-gray-900 text-white px-12 py-4 rounded-xl text-lg font-medium hover:bg-gray-800 transition-colors duration-200"
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
