import { useState } from 'react';
import MealTypeScreen from './MealTypeScreen';
import DietaryPreferencesScreen from './DietaryPreferencesScreen';
import GoalsScreen from './GoalsScreen';
import MealPlanGeneratingScreen from './MealPlanGeneratingScreen';

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

  const handleGoalsSubmit = async (selectedGoals: string[]) => {
    const finalData = { ...onboardingData, goals: selectedGoals };
    setOnboardingData(prev => ({ ...prev, goals: selectedGoals }));

    setCurrentStep(3); // Move to loading screen

    try {
      const response = await fetch('http://localhost:8000/meal-planning/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meal_types: finalData.mealTypes,
          dietary_preferences: finalData.dietaryPreferences,
          goals: finalData.goals
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const mealPlan = await response.json();
      console.log('Generated meal plan:', mealPlan);

      // TODO: Handle successful meal plan generation (e.g., navigate to meal plan view)

    } catch (error) {
      console.error('Error generating meal plan:', error);
      // TODO: Handle error state (e.g., show error message to user)
    }
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
      {currentStep === 3 && (
        <MealPlanGeneratingScreen />
      )}
    </div>
  );
}
