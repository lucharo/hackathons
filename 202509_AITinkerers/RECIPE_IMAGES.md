# Recipe Image Generation Feature

## Overview
Added automatic image generation for custom recipes to enhance the visual appeal of the nutrition coach app.

## Implementation Details

### Components Added:
1. **image_service.py** - Image generation service that:
   - Attempts to fetch relevant food images from Unsplash API (if API key provided)
   - Falls back to Foodish API for random food images
   - Returns placeholder images if all else fails

2. **Recipe Model Update** - Added optional `image_url` field to the Recipe model in `domain.py`

3. **Integration** - Modified `app.py` to generate images for each recipe after creation

4. **UI Updates**:
   - Streamlit app now displays recipe images in expandable cards
   - Images are shown with captions above the recipe details

## Configuration

### Optional: Unsplash API
For better quality and more relevant recipe images, you can provide an Unsplash API key:

1. Get a free API key from [Unsplash Developers](https://unsplash.com/developers)
2. Add to your `.env` file:
   ```
   UNSPLASH_ACCESS_KEY=your_access_key_here
   ```

Without an Unsplash key, the system automatically uses the free Foodish API as a fallback.

## How It Works

1. When recipes are generated via the `recipes_agent`, the system loops through each recipe
2. For each recipe title, it:
   - Extracts food-related keywords from the title
   - Searches Unsplash for relevant food images (if API key available)
   - Falls back to Foodish API for random food images if needed
3. The image URL is stored in the recipe's `image_url` field
4. Frontend displays the images in the recipe cards

## API Endpoints Used

- **Unsplash Search API**: `https://api.unsplash.com/search/photos`
  - Searches for food images matching recipe titles
  - Requires API key for authentication

- **Foodish API**: `https://foodish-api.com/api`
  - Free, no authentication required
  - Provides random food images as fallback

## Testing

Run the test script to verify image generation:
```bash
cd 202509_AITinkerers
uv run python test_image_generation.py
```

## Future Enhancements

1. **AI-Generated Images**: Integrate with image generation models like:
   - DALL-E 3 for custom recipe visualizations
   - Stable Diffusion for fast local generation
   - Replicate's food-specific models

2. **Image Caching**: Implement local caching to reduce API calls

3. **User Upload**: Allow users to upload their own recipe images

4. **Smart Matching**: Use recipe ingredients to improve image search relevance