import { useState } from 'react';
import MealTypeScreen from './MealTypeScreen';
import DietaryPreferencesScreen from './DietaryPreferencesScreen';
import GoalsScreen from './GoalsScreen';

export interface OnboardingData {
  mealTypes: string[];
  dietaryPreferences: string[];
  goals: string[];
}

export default function OnboardingFlow() {
  const [currentStep, setCurrentStep] = useState(0);
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    mealTypes: [],
    dietaryPreferences: [],
    goals: []
  });

  const handleMealTypesSubmit = (selectedTypes: string[]) => {
    setOnboardingData(prev => ({ ...prev, mealTypes: selectedTypes }));
    setCurrentStep(1);
  };

  const handleDietaryPreferencesSubmit = (selectedPreferences: string[]) => {
    setOnboardingData(prev => ({ ...prev, dietaryPreferences: selectedPreferences }));
    setCurrentStep(2);
  };

  const handleGoalsSubmit = (selectedGoals: string[]) => {
    setOnboardingData(prev => ({ ...prev, goals: selectedGoals }));
    // TODO: Send data to backend and proceed to main app
    console.log('Onboarding complete:', { ...onboardingData, goals: selectedGoals });
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentStep === 0 && (
        <MealTypeScreen 
          onSubmit={handleMealTypesSubmit}
          initialSelected={onboardingData.mealTypes}
        />
      )}
      {currentStep === 1 && (
        <DietaryPreferencesScreen 
          onSubmit={handleDietaryPreferencesSubmit}
          onBack={handleBack}
          initialSelected={onboardingData.dietaryPreferences}
        />
      )}
      {currentStep === 2 && (
        <GoalsScreen 
          onSubmit={handleGoalsSubmit}
          onBack={handleBack}
          initialSelected={onboardingData.goals}
        />
      )}
    </div>
  );
}
