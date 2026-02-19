from django import forms

class EncodeForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter your secret message here...'}),
        label="Message to Hide",
        max_length=1000,
        required=True
    )
    secret_key = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter a secret key'}),
        label="Encryption Key",
        max_length=50,
        required=True
    )
    image = forms.ImageField(
        label="Cover Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )

class DecodeForm(forms.Form):
    image = forms.ImageField(
        label="Steganographic Image",
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        required=True
    )
    method = forms.ChoiceField(
        label="Steganography Method",
        choices=[('LSB', 'LSB (Least Significant Bit)'), ('DCT', 'DCT (Discrete Cosine Transform)')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='LSB'
    )
    compress = forms.BooleanField(
        label="Compress Message (Zlib)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    secret_key = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter the secret key to decrypt'}),
        label="Decryption Key",
        max_length=50,
        required=True
    )
