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
  const [copied, setCopied] = useState(false);
  const [addingToCart, setAddingToCart] = useState(false);
  const [cartSuccess, setCartSuccess] = useState(false);
  const [picnicEnabled, setPicnicEnabled] = useState(false);

  useEffect(() => {
    const fetchIngredients = async () => {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

        // Check if Picnic integration should be enabled based on API base URL
        // Enable if localhost/127.0.0.1 (local development), disable otherwise (production)
        const isLocalDevelopment = Boolean(apiBaseUrl && (
          apiBaseUrl.includes('localhost') ||
          apiBaseUrl.includes('127.0.0.1') ||
          apiBaseUrl.includes('0.0.0.0')
        ));
        setPicnicEnabled(isLocalDevelopment);

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

  const formatIngredientsForClipboard = () => {
    const greeting = "Hey! Please could you order me the following ingredients via my Picnic account:\n\n";
    const ingredientsList = ingredients
      .map(ingredient => `• ${ingredient.name} - ${formatQuantity(ingredient.qty, ingredient.unit)}`)
      .join('\n');
    return greeting + ingredientsList;
  };

  const handleCopyToClipboard = async () => {
    try {
      const formattedText = formatIngredientsForClipboard();
      await navigator.clipboard.writeText(formattedText);
      setCopied(true);
      
      // Reset the copied state after 2 seconds
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = formatIngredientsForClipboard();
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    }
  };

  const handleAddToCart = async () => {
    setAddingToCart(true);
    try {
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
      const response = await fetch(`${apiBaseUrl}/buy-ingredients`, {
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
      console.log('Cart response:', data);

      if (data.success) {
        setCartSuccess(true);
        setTimeout(() => {
          setCartSuccess(false);
        }, 3000);
      } else {
        throw new Error(data.message || 'Failed to add to cart');
      }

    } catch (err) {
      console.error('Error adding to cart:', err);
      alert('Failed to add ingredients to Picnic cart. Please try again.');
    } finally {
      setAddingToCart(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Ingredients List
          </h1>
          <p className="text-gray-600">
            Your personalized shopping list based on your meal plan
          </p>
        </div>

        {/* Action Buttons - Above shopping list box */}
        {ingredients.length > 0 && (
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            {/* Add to Picnic Cart Button - Only show if MCP is enabled */}
            {picnicEnabled && (
              <button
                onClick={handleAddToCart}
                disabled={addingToCart}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-sm hover:shadow-md ${
                  cartSuccess
                    ? 'bg-green-500 text-white border border-green-600'
                    : addingToCart
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-orange-600 text-white hover:bg-orange-700'
                }`}
              >
                {cartSuccess ? (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Added to Picnic Cart!
                  </>
                ) : addingToCart ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Adding to cart... (this may take a few minutes)
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5M7 13v6a2 2 0 002 2h6a2 2 0 002-2v-6" />
                    </svg>
                    Add to Picnic Cart
                  </>
                )}
              </button>
            )}

            {/* Copy Button */}
            <button
              onClick={handleCopyToClipboard}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-200 shadow-sm hover:shadow-md ${
                copied
                  ? 'bg-green-500 text-white border border-green-600'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {copied ? (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Copied!
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy Shopping List
                </>
              )}
            </button>
          </div>
        )}

        {/* Simple Ingredients List */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Your Shopping List</h2>
          </div>
          
          {ingredients.length === 0 ? (
            <p className="text-gray-500 text-center text-sm">No ingredients found.</p>
          ) : (
            <>
              <ul className="space-y-1">
                {ingredients.map((ingredient, index) => (
                  <li key={index} className="flex justify-between items-center py-1.5 border-b border-gray-100 last:border-b-0">
                    <span className="capitalize text-sm text-gray-800">{ingredient.name}</span>
                    <span className="text-gray-600 text-sm">{formatQuantity(ingredient.qty, ingredient.unit)}</span>
                  </li>
                ))}
              </ul>
            </>
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
