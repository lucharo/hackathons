import { useState } from 'react';

interface DietaryPreferencesScreenProps {
  onSubmit: (selectedPreferences: string[]) => void;
  onBack: () => void;
  initialSelected: string[];
}

const dietaryPreferences = [
  'High protein',
  'Low carb',
  'Low calorie',
  'Low salt',
  'Plant based',
  'Low sugar'
];

export default function DietaryPreferencesScreen({ onSubmit, onBack, initialSelected }: DietaryPreferencesScreenProps) {
  const [selectedPreferences, setSelectedPreferences] = useState<string[]>(initialSelected);

  const togglePreference = (preference: string) => {
    setSelectedPreferences(prev => 
      prev.includes(preference) 
        ? prev.filter(p => p !== preference)
        : [...prev, preference]
    );
  };

  const handleContinue = () => {
    onSubmit(selectedPreferences);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="flex-1 max-w-2xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Do you have any dietary preferences?
          </h1>
          <p className="text-lg text-gray-600 max-w-lg mx-auto">
            Please select from the options below. You can always change them later.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
          {dietaryPreferences.map((preference) => (
            <button
              key={preference}
              onClick={() => togglePreference(preference)}
              className={`p-6 rounded-xl text-left transition-all duration-200 font-medium text-lg ${
                selectedPreferences.includes(preference)
                  ? 'bg-green-500 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
              }`}
            >
              {preference}
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
