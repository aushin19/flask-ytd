import base64

def encode_cookies(file_path):
    with open(file_path, 'rb') as file:
        encoded_cookies = base64.b64encode(file.read()).decode('utf-8')
    return encoded_cookies

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python encode_cookies.py path/to/cookies.txt")
        sys.exit(1)
    file_path = sys.argv[1]
    encoded = encode_cookies(file_path)
    print(encoded)