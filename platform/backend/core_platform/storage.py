"""
Core Platform Storage Service
=============================
File storage interface for the core platform.
"""

import asyncio
import logging
import os
import aiofiles
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class StorageBackend(Enum):
    """Storage backend types."""
    LOCAL_FILE = "local_file"
    S3 = "s3"
    GCS = "gcs"
    AZURE_BLOB = "azure_blob"


@dataclass
class StorageConfig:
    """Storage configuration."""
    backend: StorageBackend = StorageBackend.LOCAL_FILE
    base_path: str = "/tmp/taxpoynt_storage"
    max_file_size_mb: int = 100
    allowed_extensions: List[str] = None
    create_directories: bool = True
    
    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.json', '.csv', '.pdf', '.xml', '.txt', '.log']


class FileStorage:
    """
    File storage service for the TaxPoynt platform.
    
    Provides a unified interface for file storage operations
    across different backends (local, cloud storage, etc.).
    """
    
    def __init__(self, config: Optional[StorageConfig] = None):
        """
        Initialize file storage.
        
        Args:
            config: Storage configuration
        """
        self.config = config or StorageConfig()
        self.is_initialized = False
        self._base_path = Path(self.config.base_path)
        
    async def initialize(self) -> bool:
        """
        Initialize the storage backend.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self.config.backend == StorageBackend.LOCAL_FILE:
                # Ensure base directory exists
                if self.config.create_directories:
                    self._base_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"File storage initialized with base path: {self._base_path}")
                
                # Test write permissions
                test_file = self._base_path / ".storage_test"
                test_file.write_text("test")
                test_file.unlink()
                
                self.is_initialized = True
                return True
            else:
                logger.warning(f"Storage backend {self.config.backend} not implemented yet")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize file storage: {e}")
            return False
    
    async def save_file(self, file_path: str, content: Union[str, bytes], 
                       create_dirs: bool = True) -> bool:
        """
        Save file to storage.
        
        Args:
            file_path: Relative path to save the file
            content: File content (string or bytes)
            create_dirs: Create intermediate directories if they don't exist
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Validate file path and extension
            if not self._validate_file_path(file_path):
                logger.error(f"Invalid file path: {file_path}")
                return False
            
            # Calculate full path
            full_path = self._base_path / file_path.lstrip('/')
            
            # Create directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Validate file size
            content_size = len(content.encode() if isinstance(content, str) else content)
            if content_size > self.config.max_file_size_mb * 1024 * 1024:
                logger.error(f"File too large: {content_size} bytes > {self.config.max_file_size_mb}MB")
                return False
            
            # Save file
            if isinstance(content, str):
                async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            else:
                async with aiofiles.open(full_path, 'wb') as f:
                    await f.write(content)
            
            logger.info(f"File saved successfully: {full_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {e}")
            return False
    
    async def read_file(self, file_path: str) -> Optional[Union[str, bytes]]:
        """
        Read file from storage.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            File content or None if not found
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            full_path = self._base_path / file_path.lstrip('/')
            
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return None
            
            # Try to read as text first, fallback to binary
            try:
                async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            except UnicodeDecodeError:
                async with aiofiles.open(full_path, 'rb') as f:
                    return await f.read()
                    
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            full_path = self._base_path / file_path.lstrip('/')
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    async def list_files(self, directory: str = "", pattern: str = "*") -> List[str]:
        """
        List files in a directory.
        
        Args:
            directory: Directory to list (relative to base path)
            pattern: File pattern to match
            
        Returns:
            List of relative file paths
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            full_dir = self._base_path / directory.lstrip('/')
            
            if not full_dir.exists():
                return []
            
            files = []
            for path in full_dir.glob(pattern):
                if path.is_file():
                    relative_path = path.relative_to(self._base_path)
                    files.append(str(relative_path))
            
            return sorted(files)
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return []
    
    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            File information dict or None if not found
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            full_path = self._base_path / file_path.lstrip('/')
            
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            return {
                "path": file_path,
                "size_bytes": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None
    
    def _validate_file_path(self, file_path: str) -> bool:
        """
        Validate file path for security and format.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic security checks
        if '..' in file_path or file_path.startswith('/'):
            return False
        
        # Check file extension if restrictions are configured
        if self.config.allowed_extensions:
            path = Path(file_path)
            if path.suffix.lower() not in self.config.allowed_extensions:
                return False
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform storage health check.
        
        Returns:
            Health status dictionary
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            # Test basic operations
            test_path = "health_check_test.txt"
            test_content = "health_check"
            
            # Test write
            write_success = await self.save_file(test_path, test_content)
            
            # Test read
            read_content = await self.read_file(test_path) if write_success else None
            read_success = read_content == test_content
            
            # Test delete
            delete_success = await self.delete_file(test_path) if write_success else False
            
            # Calculate storage usage
            total_files = len(await self.list_files())
            
            return {
                "status": "healthy" if all([write_success, read_success, delete_success]) else "unhealthy",
                "backend": self.config.backend.value,
                "base_path": str(self._base_path),
                "is_initialized": self.is_initialized,
                "total_files": total_files,
                "operations": {
                    "write": write_success,
                    "read": read_success, 
                    "delete": delete_success
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "is_initialized": self.is_initialized
            }


# Global file storage instance
_file_storage: Optional[FileStorage] = None


def get_file_storage() -> FileStorage:
    """
    Get global file storage instance.
    
    Returns:
        FileStorage instance
    """
    global _file_storage
    if _file_storage is None:
        _file_storage = FileStorage()
    return _file_storage


def initialize_file_storage(config: Optional[StorageConfig] = None) -> FileStorage:
    """
    Initialize global file storage.
    
    Args:
        config: Optional storage configuration
        
    Returns:
        FileStorage instance
    """
    global _file_storage
    _file_storage = FileStorage(config)
    return _file_storage


# Export main class for direct import
FileStorage = FileStorage