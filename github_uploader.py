
import aiohttp
import logging
from typing import Callable, Optional
import json
import io

logger = logging.getLogger(__name__)

class GitHubUploader:
    def __init__(self, token: str, repo: str, release_tag: str):
        self.token = token
        self.repo = repo
        self.release_tag = release_tag
        self.api_url = "https://api.github.com"
        self.upload_url = "https://uploads.github.com"
        
    async def get_release_info(self) -> dict:
        """Get release information by tag"""
        url = f"{self.api_url}/repos/{self.repo}/releases/tags/{self.release_tag}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    raise Exception(f"Release with tag '{self.release_tag}' not found")
                elif response.status != 200:
                    raise Exception(f"Failed to get release info: HTTP {response.status}")
                
                return await response.json()

    async def delete_existing_asset(self, release_id: int, filename: str) -> bool:
        """Delete existing asset if it exists"""
        url = f"{self.api_url}/repos/{self.repo}/releases/{release_id}/assets"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return False
                
                assets = await response.json()
                for asset in assets:
                    if asset['name'] == filename:
                        # Delete the asset
                        delete_url = f"{self.api_url}/repos/{self.repo}/releases/assets/{asset['id']}"
                        async with session.delete(delete_url, headers=headers) as delete_response:
                            logger.info(f"Deleted existing asset: {filename}")
                            return delete_response.status == 204
                
                return False

    async def upload_asset(self, file_data: bytes, filename: str, progress_callback: Optional[Callable] = None) -> str:
        """Upload file as release asset"""
        try:
            # Get release info
            release_info = await self.get_release_info()
            release_id = release_info['id']
            upload_url_template = release_info['upload_url']
            
            # Remove existing asset if it exists
            await self.delete_existing_asset(release_id, filename)
            
            # Prepare upload URL
            upload_url = upload_url_template.replace('{?name,label}', f'?name={filename}')
            
            headers = {
                "Authorization": f"token {self.token}",
                "Content-Type": "application/octet-stream",
                "Content-Length": str(len(file_data))
            }
            
            # Create a custom data reader that tracks progress
            class ProgressData:
                def __init__(self, data: bytes, callback: Optional[Callable] = None):
                    self.data = data
                    self.callback = callback
                    self.total_size = len(data)
                    self.uploaded = 0
                
                async def read(self, size: int = 8192) -> bytes:
                    if self.uploaded >= self.total_size:
                        return b''
                    
                    chunk_size = min(size, self.total_size - self.uploaded)
                    chunk = self.data[self.uploaded:self.uploaded + chunk_size]
                    self.uploaded += len(chunk)
                    
                    if self.callback and chunk:
                        self.callback(self.uploaded)
                    
                    return chunk

            # Upload with progress tracking using chunked approach
            async with aiohttp.ClientSession() as session:
                # For aiohttp, we need to use a generator or async iterator
                async def data_generator():
                    chunk_size = 1024 * 1024  # 1MB chunks
                    uploaded = 0
                    
                    while uploaded < len(file_data):
                        chunk_end = min(uploaded + chunk_size, len(file_data))
                        chunk = file_data[uploaded:chunk_end]
                        uploaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(uploaded)
                        
                        yield chunk

                async with session.post(upload_url, headers=headers, data=data_generator()) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        raise Exception(f"Failed to upload asset: HTTP {response.status} - {error_text}")
                    
                    result = await response.json()
                    download_url = result['browser_download_url']
                    logger.info(f"Successfully uploaded {filename} to GitHub")
                    return download_url
                    
        except Exception as e:
            logger.error(f"Error uploading to GitHub: {e}")
            raise
