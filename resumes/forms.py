from django import forms
from .extraction import validate_pdf

class UploadForm(forms.Form):
    resume = forms.FileField(label='PDF resume', validators=[validate_pdf],
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf,application/pdf'}))
    consent = forms.BooleanField(label='I am authorized to upload this resume and send its text to OpenAI for parsing.')
