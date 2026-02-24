# from django import forms

# class EncodeForm(forms.Form):
#     message = forms.CharField(
#         widget=forms.Textarea(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 placeholder-gray-600 transition duration-200 resize-none outline-none hover:border-white/20', 
#             'placeholder': 'Enter the secret message...',
#             'rows': 4
#         }),
#         label="Message to Hide"
#     )
#     secret_key = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 placeholder-gray-600 transition duration-200 outline-none hover:border-white/20', 
#             'placeholder': '••••••••'
#         }),
#         label="Encryption Key"
#     )
#     image = forms.ImageField(
#         label="Cover Image",
#         widget=forms.ClearableFileInput(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-white/10 file:text-white hover:file:bg-white/20 transition duration-200 cursor-pointer'
#         }),
#         required=True
#     )
#     method = forms.ChoiceField(
#         label="Steganography Method",
#         choices=[('LSB', 'LSB (Least Significant Bit)'), ('DCT', 'DCT (Discrete Cosine Transform)')],
#         widget=forms.Select(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 transition duration-200 outline-none cursor-pointer hover:border-white/20'
#         }),
#         initial='LSB'
#     )
#     compress = forms.BooleanField(
#         label="Compress Message (Zlib)",
#         required=False,
#         initial=False,
#         widget=forms.CheckboxInput(attrs={
#             'class': 'w-4 h-4 rounded border-white/10 bg-black/20 text-blue-500 focus:ring-offset-black focus:ring-1 focus:ring-blue-500 transition duration-200 cursor-pointer'
#         })
#     )

# class DecodeForm(forms.Form):
#     image = forms.ImageField(
#         label="Steganographic Image",
#         widget=forms.ClearableFileInput(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-white/10 file:text-white hover:file:bg-white/20 transition duration-200 cursor-pointer'
#         }),
#         required=True
#     )
#     secret_key = forms.CharField(
#         widget=forms.PasswordInput(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 placeholder-gray-600 transition duration-200 outline-none hover:border-white/20', 
#             'placeholder': '••••••••'
#         }),
#         label="Decryption Key"
#     )
#     method = forms.ChoiceField(
#         label="Steganography Method",
#         choices=[('LSB', 'LSB (Least Significant Bit)'), ('DCT', 'DCT (Discrete Cosine Transform)')],
#         widget=forms.Select(attrs={
#             'class': 'w-full px-3 py-2 bg-black/20 border border-white/10 rounded-lg focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm text-gray-200 transition duration-200 outline-none cursor-pointer hover:border-white/20'
#         }),
#         initial='LSB'
#     )
