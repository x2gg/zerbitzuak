from typing import Tuple
import bcrypt
import hashlib
import requests
import uuid
import re
import mimetypes
import os
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request, UploadFile, Request
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
HIBP_TIMEOUT = settings.HIBP_TIMEOUT
MAX_FILE_SIZE_MB = settings.MAX_FILE_SIZE_MB

def verify_password(plain_password: str, hashed_password: str) -> bool:
	"""Verify a password against a hash."""
	return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
	"""Hash a password."""
	hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
	return hash

def check_pwd_security(password: str, timeout: int = HIBP_TIMEOUT) -> Tuple[bool, int]:
    """
    Check if a password has been previously exposed.
    
    This function makes a GET request to the Pwned Passwords API
    with the first 5 characters of the SHA-1 hash of the password.
    If the response contains the full hash, it returns False and the count
    of how many times the password has been seen.
    
    If the request times out, it returns True and 0.
    """
    try:
        sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        
        response = requests.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=timeout
        )
        
        if response.status_code == 200:
            for line in response.text.splitlines():
                hash_suffix, count = line.split(':')
                if hash_suffix == suffix:
                    return False, int(count)
        
        return True, 0
        
    except:
        # If the request fails for any reason, allow the user to register
        return True, 0

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
	"""Get the current user from the JWT token."""
	credentials_exception = HTTPException(
		status_code=status.HTTP_401_UNAUTHORIZED,
		detail="Could not validate credentials",
		headers={"WWW-Authenticate": "Bearer"},
	)
	
	try:
		payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
		username: str = payload.get("sub")
		if not username:
			raise credentials_exception
		return payload
	except JWTError:
		raise credentials_exception

def get_username_from_apisix_request(request: Request) -> str:
	"""Return the username extracted from APISIX request headers.

	APISIX sets the `X-Consumer-Username` header once the user is authenticated.
	If the header is not present we raise 401.
	"""
	username = request.headers.get("x-consumer-username")
	if not username:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="User authentication failed - No consumer username in headers"
		)
	return username


def ensure_admin_request(request: Request):
	username = get_username_from_apisix_request(request)
	if not username or username != settings.CRUD_ADMIN:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Could not validate credentials",
			headers={"WWW-Authenticate": "Bearer"},
		)


async def validate_file_type(file: UploadFile) -> bool:
    """
    Validate that the file type is allowed (only txt or pdf).
    
    Args:
        file: The UploadFile to validate.
    
    Returns:
        bool: True if the file type is allowed, False otherwise.
        
    Raises:
        HTTPException: If the file type is not allowed.
    """
    ALLOWED_MIME_TYPES = {
        'text/plain',  # .txt
        'application/pdf'  # .pdf
    }
    
    # Get the file extension and MIME type
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    if not mime_type or mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Additional check for file extension to prevent MIME type spoofing
    if file_extension not in ['txt', 'pdf']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension. Only .txt and .pdf files are allowed."
        )
    
    return True


async def sanitize_filename(file: UploadFile) -> Tuple[str, str]:
    """
    Sanitize filename to prevent path traversal attacks and avoid file collisions.
    
    Args:
        file: The UploadFile to sanitize.
        
    Returns:
        Tuple[str, str]: A tuple containing (original_filename, sanitized_filename)
        
    Raises:
        HTTPException: If the filename contains dangerous characters.
    """
    original_filename = file.filename or "unknown_file"
    
    # Check for dangerous characters that could be used in path traversal attacks
    dangerous_patterns = [r'\.\./', r'\.\\', r'\.\.', r'/', r'\\']
    
    for pattern in dangerous_patterns:
        if re.search(pattern, original_filename, re.IGNORECASE):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Filename contains dangerous characters that could lead to path traversal attacks"
            )
    
    # Extract file extension
    file_extension = ""
    if "." in original_filename:
        name_part, extension_part = original_filename.rsplit(".", 1)
        file_extension = f".{extension_part.lower()}"
    
    # Generate a random UUID-based filename
    random_uuid = str(uuid.uuid4())
    sanitized_filename = f"{random_uuid}{file_extension}"
    
    return original_filename, sanitized_filename


async def verify_file_size(file: UploadFile) -> bool:
    """
    Verify that the file does not exceed the maximum size specified in MB.
    
    The file is read in chunks to avoid loading everything into memory.
    If the file exceeds the maximum size, an HTTPException is raised.
    
    Args:
        file: The UploadFile received in the endpoint.
    
    Returns:
        True if the file size is valid, False otherwise.
    
    Raises:
        HTTPException: If the file exceeds the maximum size.
    """
    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes
    current_size = 0
    
    try:
        # Read the file in chunks to avoid loading everything into memory
        while chunk := await file.read(1024 * 1024):  # Read in chunks of 1MB
            current_size += len(chunk)
            if current_size > max_size_bytes:
                raise HTTPException(status_code=413, detail=f"The file exceeds the maximum size of {MAX_FILE_SIZE_MB} MB")
        
        # If everything is OK, return to the beginning of the file for later processing
        await file.seek(0)
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying the file: {str(e)}")