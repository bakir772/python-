import random
print("Welcome to Guessing Game")
secret_number = random.randint(1, 10)
attempt = 0
while True:
    guss = int( input( "Enter num between 1 to 10"))
    attempt += 1
    
    if guss == secret_number:
        print("correct answer")
        break
    elif guss > secret_number:
        print("too high try again")
    else:
        print("too low try again")