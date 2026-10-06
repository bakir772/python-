numbers = input("enter number separated by space").split()
newlist = []
for num in numbers:
    newlist.append(int(num))
print("NewList", newlist)
positive = 0
nigative = 0
zero = 0
for num in newlist:
    if num > 0:
        positive += 1
    elif num < 0:
        nigative += 1
    else:  # elif num == 0:
        zero += 1
print("+", positive)
print("-", nigative)
print("zero", zero)