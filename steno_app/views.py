from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .forms import EncodeForm, DecodeForm
from .utils import encrypt_message, decrypt_message, text_to_morse, morse_to_text, encode_image, decode_image
from PIL import Image
import io
import binascii

from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def home(request):
    return render(request, 'steno_app/index.html', {
        'encode_form': EncodeForm(),
        'decode_form': DecodeForm()
    })

@login_required
def encode_view(request):
    if request.method == 'POST':
        form = EncodeForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                message = form.cleaned_data['message']
                key = form.cleaned_data['secret_key']
                image_file = form.cleaned_data['image']

                # 1. Encrypt Message
                # encrypt_message returns hex string of IV + Encrypted Data
                encrypted_hex = encrypt_message(message, key)
                
                # 2. Convert Hex String to Morse Code
                morse_msg = text_to_morse(encrypted_hex)
                
                # 3. Encode into Image
                original_img = Image.open(image_file)
                # Ensure image is RGB (remove alpha channel if present)
                if original_img.mode != 'RGB':
                    original_img = original_img.convert('RGB')
                    
                encoded_img = encode_image(original_img, morse_msg)
                
                # Prepare image for display/download
                buffer = io.BytesIO()
                encoded_img.save(buffer, format="PNG") # PNG is lossless
                buffer.seek(0)
                
                # Encode to Base64
                encoded_base64 = binascii.b2a_base64(buffer.getvalue()).decode('utf-8').strip()
                
                return render(request, 'steno_app/result.html', {
                    'encoded_image': encoded_base64
                })
                
            except Exception as e:
                return render(request, 'steno_app/index.html', {
                    'encode_form': form,
                    'decode_form': DecodeForm(),
                    'error': f"Encoding Error: {str(e)}"
                })
        else:
             return render(request, 'steno_app/index.html', {
                'encode_form': form,
                'decode_form': DecodeForm(),
                'error': "Form Validation Failed."
            })
    
    return redirect('home')

@login_required
def decode_view(request):
    if request.method == 'POST':
        form = DecodeForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                key = form.cleaned_data['secret_key']
                image_file = form.cleaned_data['image']
                
                img = Image.open(image_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # 1. Extract Morse Code from Image
                extracted_morse = decode_image(img)
                
                if not extracted_morse:
                     return render(request, 'steno_app/index.html', {
                        'encode_form': EncodeForm(),
                        'decode_form': form,
                        'error': "No hidden message found or integrity check failed."
                    })
                
                # 2. Convert Morse to Hex String
                encrypted_hex = morse_to_text(extracted_morse)
                
                # 3. Decrypt Message
                decrypted_msg = decrypt_message(encrypted_hex, key)
                
                if decrypted_msg.startswith("Decryption Failed"):
                    return render(request, 'steno_app/index.html', {
                        'encode_form': EncodeForm(),
                        'decode_form': form,
                        'error': decrypted_msg
                    })

                return render(request, 'steno_app/result.html', {
                    'decrypted_message': decrypted_msg
                })
                
            except Exception as e:
                return render(request, 'steno_app/index.html', {
                    'encode_form': EncodeForm(),
                    'decode_form': form,
                    'error': f"Decoding Error: {str(e)}"
                })
        else:
             return render(request, 'steno_app/index.html', {
                'encode_form': EncodeForm(),
                'decode_form': form,
                'error': "Form Validation Failed."
            })

    return redirect('home')
