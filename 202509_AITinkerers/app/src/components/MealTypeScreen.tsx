import { useState } from 'react';

interface MealTypeScreenProps {
  onSubmit: (selectedTypes: string[]) => void;
  onBack?: () => void;
  initialSelected: string[];
}

const mealTypes = [
  'Mostly Meat',
  'Veggie',
  'Family',
  'Quick Cook',
  'Calorie Smart',
  'Pescatarian',
  'Flexitarian',
  'Protein Rich'
];

export default function MealTypeScreen({ onSubmit, onBack, initialSelected }: MealTypeScreenProps) {
  const [selectedTypes, setSelectedTypes] = useState<string[]>(initialSelected);

  const toggleMealType = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    );
  };

  const handleContinue = () => {
    onSubmit(selectedTypes);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex-1 max-w-2xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            What kind of meals do you like?
          </h1>
          <p className="text-lg text-gray-600 max-w-lg mx-auto">
            We'll adjust your meal options based on your preferences, but you can always add them back later if you change your mind.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
          {mealTypes.map((type) => (
            <button
              key={type}
              onClick={() => toggleMealType(type)}
              className={`p-6 rounded-xl text-left transition-all duration-200 font-medium text-lg ${
                selectedTypes.includes(type)
                  ? 'bg-green-500 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {type}
            </button>
          ))}
        </div>

        <div className="flex justify-between items-center">
          {onBack && (
            <button
              onClick={onBack}
              className="bg-gray-200 text-gray-700 px-8 py-4 rounded-xl text-lg font-medium hover:bg-gray-300 transition-colors duration-200"
            >
              ← Back
            </button>
          )}
          <button
            onClick={handleContinue}
            className={`bg-gray-900 text-white px-12 py-4 rounded-xl text-lg font-medium hover:bg-gray-800 transition-colors duration-200 min-w-[200px] ${!onBack ? 'mx-auto' : 'ml-auto'}`}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
