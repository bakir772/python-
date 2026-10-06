# we have tow way to this cod .
#1
text = input('enter your text')
reversed_text = ""
for loopChar in text:
    reversed_text = loopChar + reversed_text
print(reversed_text)    
# 2 
text = input('enter your text')
reversed_text = text[::-1]
print(reversed_text)    