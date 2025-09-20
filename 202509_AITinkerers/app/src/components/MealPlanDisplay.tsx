import { useState } from 'react';

export interface Nutrition {
  calories: number;
  grams_protein: number;
  grams_carbs: number;
  grams_fat: number;
}

export interface Meal {
  name: string;
  description: string;
  num_servings: number;
  nutrition: Nutrition;
  meal_type: 'breakfast' | 'lunch/dinner';
  diet_type: string;
  allergens: string[];
}

export interface MealPlan {
  meals: Meal[];
}

interface MealPlanDisplayProps {
  mealPlan: MealPlan;
  onStartOver?: () => void;
}

export default function MealPlanDisplay({ mealPlan }: MealPlanDisplayProps) {
  const [selectedMeal, setSelectedMeal] = useState<Meal | null>(null);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [feedback, setFeedback] = useState('');


  const getMealTypeIcon = (mealType: string) => {
    return mealType === 'breakfast' ? '🌅' : '🍽️';
  };

  const getDietTypeColor = (dietType: string) => {
    const colors: Record<string, string> = {
      vegetarian: 'bg-green-100 text-green-800',
      vegan: 'bg-emerald-100 text-emerald-800',
      pescatarian: 'bg-blue-100 text-blue-800',
      gluten_free: 'bg-yellow-100 text-yellow-800',
      halal: 'bg-purple-100 text-purple-800',
    };
    return colors[dietType] || 'bg-gray-100 text-gray-800';
  };

  const formatDietType = (dietType: string) => {
    return dietType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const MealCard = ({ meal }: { meal: Meal }) => (
    <div 
      className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-all duration-300 cursor-pointer border border-gray-100"
      onClick={() => setSelectedMeal(meal)}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{getMealTypeIcon(meal.meal_type)}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{meal.name}</h3>
            <p className="text-sm text-gray-600 capitalize">{meal.meal_type.replace('/', ' / ')}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-blue-600">{meal.nutrition.calories} cal</div>
          <div className="text-sm text-gray-500">{meal.num_servings} serving{meal.num_servings > 1 ? 's' : ''}</div>
        </div>
      </div>

      <p className="text-gray-700 text-sm mb-4 line-clamp-2">{meal.description}</p>

      <div className="flex flex-wrap gap-2 mb-4">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDietTypeColor(meal.diet_type)}`}>
          {formatDietType(meal.diet_type)}
        </span>
        {meal.allergens.length > 0 && (
          <span className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Contains: {meal.allergens.join(', ')}
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4 text-sm">
        <div className="text-center">
          <div className="font-semibold text-gray-900">{meal.nutrition.grams_protein}g</div>
          <div className="text-gray-500">Protein</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">{meal.nutrition.grams_carbs}g</div>
          <div className="text-gray-500">Carbs</div>
        </div>
        <div className="text-center">
          <div className="font-semibold text-gray-900">{meal.nutrition.grams_fat}g</div>
          <div className="text-gray-500">Fat</div>
        </div>
      </div>
    </div>
  );

  const MealDetailModal = () => {
    if (!selectedMeal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="text-3xl">{getMealTypeIcon(selectedMeal.meal_type)}</span>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedMeal.name}</h2>
                  <p className="text-gray-600 capitalize">{selectedMeal.meal_type.replace('/', ' / ')}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedMeal(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold mb-2">Description</h3>
              <p className="text-gray-700">{selectedMeal.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-6 mb-6">
              <div>
                <h3 className="text-lg font-semibold mb-3">Nutrition Facts</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-center border-b border-gray-200 pb-2 mb-2">
                    <span className="font-semibold">Calories</span>
                    <span className="text-xl font-bold text-blue-600">{selectedMeal.nutrition.calories}</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Protein</span>
                      <span className="font-medium">{selectedMeal.nutrition.grams_protein}g</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Carbohydrates</span>
                      <span className="font-medium">{selectedMeal.nutrition.grams_carbs}g</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Fat</span>
                      <span className="font-medium">{selectedMeal.nutrition.grams_fat}g</span>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Details</h3>
                <div className="space-y-3">
                  <div>
                    <span className="text-sm text-gray-600">Servings</span>
                    <div className="text-lg font-semibold">{selectedMeal.num_servings}</div>
                  </div>
                  <div>
                    <span className="text-sm text-gray-600">Diet Type</span>
                    <div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDietTypeColor(selectedMeal.diet_type)}`}>
                        {formatDietType(selectedMeal.diet_type)}
                      </span>
                    </div>
                  </div>
                  {selectedMeal.allergens.length > 0 && (
                    <div>
                      <span className="text-sm text-gray-600">Allergens</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedMeal.allergens.map((allergen, index) => (
                          <span key={index} className="px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            {allergen}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };


  const handleFeedbackSubmit = () => {
    alert("This feature hasn't been implemented yet.");
    setShowFeedbackModal(false);
    setFeedback('');
  };


  const FeedbackModal = () => {
    if (!showFeedbackModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <div className="bg-white rounded-2xl max-w-md w-full">
          <div className="p-6">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-gray-900">Update Your Meal Plan</h2>
                <p className="text-gray-600 text-sm mt-1">Tell us what you'd like to change about your meal plan</p>
              </div>
              <button
                onClick={() => {
                  setShowFeedbackModal(false);
                  setFeedback('');
                }}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>

            <div className="mb-6">
              <label htmlFor="feedback-textarea" className="block text-sm font-medium text-gray-700 mb-2">
                Your feedback
              </label>
              <div className="relative">
                <textarea
                  id="feedback-textarea"
                  key="feedback-textarea"
                  value=""
                  disabled
                  placeholder="What would you like to change?"
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 text-gray-500 cursor-not-allowed resize-none opacity-60"
                />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <span className="text-gray-500 font-medium">Feature not yet implemented</span>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowFeedbackModal(false);
                  setFeedback('');
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleFeedbackSubmit}
                disabled={true}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-500 rounded-lg font-medium cursor-not-allowed"
              >
                Submit
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };


  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Your Personalized Meal Plan</h1>
          <p className="text-gray-600">Here are your customized meals based on your preferences</p>
        </div>


        {/* All Meals Section */}
        <div className="mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mealPlan.meals.map((meal, index) => (
              <MealCard key={`meal-${index}`} meal={meal} />
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mt-12">
          <button
            onClick={() => setShowFeedbackModal(true)}
            className="px-8 py-3 bg-gray-600 text-white rounded-lg font-semibold hover:bg-gray-700 transition-colors"
          >
            Update this plan
          </button>
          <button className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors">
            Buy the ingredients!
          </button>
        </div>
      </div>

      {/* Meal Detail Modal */}
      <MealDetailModal />
      
      {/* Feedback Modal */}
      <FeedbackModal />
    </div>
  );
}
