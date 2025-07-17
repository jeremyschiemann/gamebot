import httpx
from pydantic import BaseModel, HttpUrl, ValidationError
from typing import Optional

# Pydantic model for the API response
class DogImageResponse(BaseModel):
    """
    Represents the expected structure of the Dog CEO API response.
    Validates that 'message' is a valid HTTP URL and 'status' is a string.
    """
    message: HttpUrl
    status: str


class DogImageFetcher:
    """
    A utility class to asynchronously fetch a random dog image URL and its
    raw bytes from the Dog CEO API.
    """

    def __init__(self):
        """
        Initializes the DogImageFetcher. The base API URL for random images
        will be constructed dynamically based on method calls.
        """
        self._client = None # httpx.AsyncClient will be initialized when first used

    async def _get_client(self):
        """
        Internal method to get or create an httpx.AsyncClient instance.
        This ensures the client is reused across multiple calls within the
        same class instance, which is more efficient.
        """
        if self._client is None:
            self._client = httpx.AsyncClient()
        return self._client

    async def fetch_image_url(self, breed: Optional[str] = None, sub_breed: Optional[str] = None) -> HttpUrl:
        """
        Asynchronously fetches a random dog image URL from the API,
        optionally filtered by breed and sub-breed.

        Args:
            breed (str, optional): The breed of the dog to fetch an image for.
                                   If None, fetches a random image from all breeds.
            sub_breed (str, optional): The sub-breed of the dog. Requires 'breed' to be specified.

        Returns:
            HttpUrl: A Pydantic HttpUrl object representing the image URL.

        Raises:
            ValueError: If sub_breed is provided without a breed, or if the API response status is not 'success'.
            ConnectionError: If there's an issue connecting to the API.
            ValidationError: If the API response format is invalid according to the Pydantic model.
            RuntimeError: For any other unexpected errors during the fetch.
        """
        if sub_breed and not breed:
            raise ValueError("Cannot specify sub_breed without also specifying a breed.")

        if breed and sub_breed:
            api_url = f"https://dog.ceo/api/breed/{breed}/{sub_breed}/images/random"
        elif breed:
            api_url = f"https://dog.ceo/api/breed/{breed}/images/random"
        else:
            api_url = "https://dog.ceo/api/breeds/image/random" # Original random endpoint

        client = await self._get_client()
        print(f"Fetching dog image URL from {api_url}...")
        try:
            response = await client.get(api_url)
            response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses

            data = response.json()
            parsed_response = DogImageResponse(**data) # Pydantic parsing

            if parsed_response.status == "success":
                print(f"Successfully fetched URL: {parsed_response.message}")
                return parsed_response.message
            else:
                raise ValueError(f"API status was not 'success': {parsed_response.status}")

        except httpx.RequestError as e:
            raise ConnectionError(f"Network or request error while fetching API: {e}") from e
        except ValidationError as e:
            raise ValidationError(f"API response validation error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during API URL fetch: {e}") from e

    async def fetch_image_bytes(self, breed: Optional[str] = None, sub_breed: Optional[str] = None) -> bytes:
        """
        Asynchronously fetches the raw bytes of a random dog image from the API,
        optionally filtered by breed and sub-breed.
        This method first fetches the URL, then loads the image bytes from that URL.

        Args:
            breed (str, optional): The breed of the dog to fetch an image for.
            sub_breed (str, optional): The sub-breed of the dog. Requires 'breed' to be specified.

        Returns:
            bytes: The raw binary data of the dog image.

        Raises:
            ValueError: If sub_breed is provided without a breed, or if the API response status is not 'success'.
            ConnectionError: If there's an issue connecting to the API or the image URL.
            ValidationError: If the API response format is invalid.
            RuntimeError: For any other unexpected errors.
        """
        image_url = await self.fetch_image_url(breed=breed, sub_breed=sub_breed) # First get the URL

        client = await self._get_client()
        print(f"Loading image bytes from {image_url}...")
        try:
            response = await client.get(str(image_url)) # Convert HttpUrl to string for httpx
            response.raise_for_status()
            print("Image bytes loaded successfully! 🐾")
            return response.content # Return raw bytes

        except httpx.RequestError as e:
            raise ConnectionError(f"Network or request error while loading image bytes: {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during image bytes loading: {e}") from e

    async def __aenter__(self):
        """Allows the class to be used as an async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensures the httpx client is closed when exiting the context."""
        if self._client:
            await self._client.aclose()