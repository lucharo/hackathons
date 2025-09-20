import { useState } from 'react';
import MealTypeScreen from './MealTypeScreen';
import DietaryPreferencesScreen from './DietaryPreferencesScreen';
import GoalsScreen from './GoalsScreen';
import MealPlanGeneratingScreen from './MealPlanGeneratingScreen';
import MealPlanDisplay, { type MealPlan } from './MealPlanDisplay';

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
  const [generatedMealPlan, setGeneratedMealPlan] = useState<MealPlan | null>(null);

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

    // // Simulate API delay for development with example data
    // try {
    //   console.log('Using example meal plan data for development');
    //   console.log('User preferences:', {
    //     meal_types: finalData.mealTypes,
    //     dietary_preferences: finalData.dietaryPreferences,
    //     goals: finalData.goals
    //   });
      
    //   // Simulate API delay
    //   await new Promise(resolve => setTimeout(resolve, 2000));
      
    //   // Use example meal plan data
    //   const mealPlan = exampleMealPlan as MealPlan;
    //   console.log('Loaded example meal plan:', mealPlan);
      
    //   setGeneratedMealPlan(mealPlan);
    //   setCurrentStep(4); // Move to meal plan display

    // } catch (error) {
    //   console.error('Error loading example meal plan:', error);
    //   // TODO: Handle error state (e.g., show error message to user)
    // }

    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
      const response = await fetch(`${apiBaseUrl}/meal-planning/generate`, {
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
      
      setGeneratedMealPlan(mealPlan);
      setCurrentStep(4); // Move to meal plan display

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

  const handleStartOver = () => {
    setCurrentStep(0);
    setOnboardingData({
      mealTypes: [],
      dietaryPreferences: [],
      goals: []
    });
    setGeneratedMealPlan(null);
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
      {currentStep === 4 && generatedMealPlan && (
        <MealPlanDisplay 
          mealPlan={generatedMealPlan}
          onStartOver={handleStartOver}
        />
      )}
    </div>
  );
}
