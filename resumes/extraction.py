from pathlib import Path
import re

import pymupdf
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_pdf(upload):
    if Path(upload.name).suffix.lower() != '.pdf':
        raise ValidationError('Choose a PDF file.')
    if not upload.size:
        raise ValidationError('The uploaded file is empty.')
    if upload.size > settings.RESUME_MAX_BYTES:
        raise ValidationError('PDF must be no larger than 5 MB.')
    header = upload.read(5)
    upload.seek(0)
    if header != b'%PDF-':
        raise ValidationError('This file does not have a valid PDF signature.')
    return upload


def extract_text(file):
    file.seek(0)
    content = file.read(settings.RESUME_MAX_BYTES + 1)
    if len(content) > settings.RESUME_MAX_BYTES or not content.startswith(b'%PDF-'):
        raise ValidationError('Invalid or oversized PDF.')
    try:
        with pymupdf.open(stream=content, filetype='pdf') as document:
            if document.needs_pass:
                raise ValidationError('Password-protected PDFs are not supported. Upload an unlocked copy.')
            if not document.page_count:
                raise ValidationError('The PDF has no pages.')
            if document.page_count > settings.RESUME_MAX_PAGES:
                raise ValidationError('PDF must contain no more than 30 pages.')
            parts, count = [], 0
            for page in document:
                part = page.get_text(sort=True).strip()
                count += len(part)
                if count > settings.RESUME_MAX_TEXT_CHARS:
                    raise ValidationError('PDF contains too much text. Upload a shorter resume.')
                parts.append(part)
            text = '\n'.join(parts).replace('\x00', '').strip()
            if not text:
                raise ValidationError('No extractable text found. Scanned/image-only PDFs require OCR first.')
            return text
    except (pymupdf.FileDataError, RuntimeError, ValueError):
        raise ValidationError('The PDF is corrupted or unreadable.') from None


def mask_aadhaar(text):
    return re.sub(r'(?<!\d)(\d{4})[ -]?(\d{4})[ -]?(\d{4})(?!\d)', r'XXXX XXXX \3', text)
