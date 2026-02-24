from steno_app.utils import text_to_morse, morse_to_text

print("Testing Alphanumeric:")
msg = "Hello World"
m = text_to_morse(msg)
print(m)
print(morse_to_text(m))

print("\nTesting Emojis & Unicode:")
msg = "Welcome 🌍 ! áéíóú ✨"
m = text_to_morse(msg)
print(m)
print(morse_to_text(m))
