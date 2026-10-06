nums = input ('enter your number ').split()
unique = []
for item in nums:
    if item not in unique :
        unique.append(item)
print (unique) 