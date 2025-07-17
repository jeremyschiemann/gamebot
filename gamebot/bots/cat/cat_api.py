import httpx
from pydantic import BaseModel, HttpUrl, ValidationError

class CatImageResponse(BaseModel):
    id: str
    url: HttpUrl
    width: int
    height: int


class CatImageFetcher:

    def __init__(self) -> None:
        self._client = httpx.AsyncClient()
    

    async def fetch_image_url(self) -> HttpUrl:
        api_url = 'https://api.thecatapi.com/v1/images/search'
        
        print(f'Fetching cat image URL from {api_url}')

        client = self._client


        try:
            response = await client.get(api_url)
            response.raise_for_status()

            data = response.json()
            parsed_response = [CatImageResponse.model_validate(entry) for entry in data]

            if parsed_response:
                print(f'Succesfully fetched URL: {parsed_response[0].url}')
                return parsed_response[0].url
            else:
                raise ValueError(f'API response was invalid: {data}')
        except httpx.RequestError as e:
            raise ConnectionError(f"Network or request error while fetching API: {e}") from e
        except ValidationError as e:
            raise ValidationError(f"API response validation error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during API URL fetch: {e}") from e
        
    
    async def fetch_image_bytes(self) -> bytes:
        image_url = await self.fetch_image_url()
        print(f"Loading image bytes from {image_url}...")
        client = self._client
        try:
            response = await client.get(str(image_url)) # Convert HttpUrl to string for httpx
            response.raise_for_status()
            print("Image bytes loaded successfully! 🐈")
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
        await self._client.aclose()