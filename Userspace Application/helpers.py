from passlib.handlers.pbkdf2 import pbkdf2_sha256


def hash_pass_code(code: []) -> str:
    return pbkdf2_sha256.hash(''.join(str(k) for k in code), salt=b'', rounds=5000)


if __name__ == '__main__':
    print(hash_pass_code([5, 5, 5, 5]))