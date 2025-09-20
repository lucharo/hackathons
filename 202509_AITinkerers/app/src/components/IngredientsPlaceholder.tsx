interface IngredientsPlaceholderProps {
  onBack: () => void;
}

export default function IngredientsPlaceholder({ onBack }: IngredientsPlaceholderProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <div className="mb-6">
            <div className="text-6xl mb-4">🛒</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Ingredient Shopping
            </h1>
            <p className="text-gray-600">
              This feature is not yet implemented. We're working on integrating with grocery delivery services to make shopping for your meal plan ingredients seamless!
            </p>
          </div>
          
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Coming Soon:</h3>
              <ul className="text-sm text-gray-600 space-y-1 text-left">
                <li>• Automatic ingredient list generation</li>
                <li>• Integration with delivery services</li>
                <li>• Smart quantity calculations</li>
                <li>• Cost estimation</li>
              </ul>
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
    </div>
  );
}
