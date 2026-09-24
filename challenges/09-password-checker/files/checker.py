#!/usr/bin/env python3
# Oasis Vault - Password Checker v1.0

SECRET = [126, 107, 99, 104, 107, 98, 81, 88, 25, 92, 25, 88, 89, 27, 68, 77, 117, 27, 89, 117, 76, 95, 68, 87]
KEY = 42


def check(password):
    if len(password) != len(SECRET):
        return False
    for i in range(len(password)):
        if ord(password[i]) ^ KEY != SECRET[i]:
            return False
    return True


def main():
    print("=== Oasis Vault ===")
    password = input("Enter the password: ")
    if check(password):
        print("Access granted! The password is the flag.")
    else:
        print("Access denied.")


if __name__ == "__main__":
    main()
