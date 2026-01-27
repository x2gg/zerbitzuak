from pydantic import BaseModel, Field
from fastapi import File

from app.core.config import settings


class TextRequest(BaseModel):
	text: str = Field(min_length=settings.TEXT_MIN_LENGTH, max_length=settings.TEXT_MAX_LENGTH)

# class FileRequest(BaseModel):
# 	file: File
