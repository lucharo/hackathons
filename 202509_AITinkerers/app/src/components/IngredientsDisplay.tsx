import { useState, useEffect } from 'react';
import type { Meal } from './MealPlanDisplay';

interface Ingredient {
  name: string;
  qty: number;
  unit: string;
}

interface IngredientsDisplayProps {
  meals: Meal[];
  onBack: () => void;
}

export default function IngredientsDisplay({ meals, onBack }: IngredientsDisplayProps) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
        const response = await fetch(`${apiBaseUrl}/buy-ingredients/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            meals: meals
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Generated ingredients:', data);
        setIngredients(data.ingredients);
      } catch (err) {
        console.error('Error fetching ingredients:', err);
        setError('Failed to generate ingredient list. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchIngredients();
  }, [meals]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="mb-6">
              <div className="text-6xl mb-4">🛒</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Generating Shopping List
              </h1>
              <p className="text-gray-600">
                We're analyzing your meals and creating a personalized ingredient list...
              </p>
            </div>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full mx-4">
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <div className="mb-6">
              <div className="text-6xl mb-4">❌</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Oops! Something went wrong
              </h1>
              <p className="text-gray-600 mb-4">
                {error}
              </p>
            </div>
            <button
              onClick={onBack}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Back to Meal Plan
            </button>
          </div>
        </div>
      </div>
    );
  }

  const formatQuantity = (qty: number, unit: string) => {
    return `${qty} ${unit}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Ingredients List
          </h1>
        </div>

        {/* Simple Ingredients List */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          {ingredients.length === 0 ? (
            <p className="text-gray-500 text-center">No ingredients found.</p>
          ) : (
            <ul className="space-y-2">
              {ingredients.map((ingredient, index) => (
                <li key={index} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                  <span className="capitalize">{ingredient.name}</span>
                  <span className="text-gray-600">{formatQuantity(ingredient.qty, ingredient.unit)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={onBack}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Meal Plan
          </button>
        </div>
      </div>
    </div>
  );
}
