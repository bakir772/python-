#1--
numbers = input("enter num separated by space").split()
newNumbers = []
for x in numbers:
    newNumbers.append(int(x))
total = 0
count = 0
for num in newNumbers:
    total += num
    count += 1
if count >0 :
    avg = total / count
    print("Avg:", avg)
else :
    print('eror')    

#2--    
newNumbers = [ int(x) for x in input("enter num separated by space").split()] 
age = sum(newNumbers)/len(newNumbers)
print('Age',age )