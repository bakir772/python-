# التحقق من قوة الرمز
Password = input("Enter your password: ")
# شروط أولية
has_upper = False
has_lower = False
has_number = False
has_enough = len(Password) >= 8
# حلقة للتحقق من الرموز
for char in Password:
    if char.isupper():
        has_upper = True
    if char.islower():
        has_lower = True
    if char.isdigit():
        has_number = True
# التحقق النهائي
if has_enough and has_number and has_lower and has_upper:
    print("Strong password")
else:
    print("Weak password")
    if not has_enough:
        print("At least 8 char")
    if not has_upper:
        print("At least 1 upper")
    if not has_lower:
        print("At least 1 lower")
    if not has_number:
        print("At least 1 number")