import random
OPTS = ["a pet shark", "mrbeast's youtube channel", "a first edition holographic charizard"]
ANS = ["a pet shark", "pet shark", "mrbeast's youtube channel", "a first edition holographic charizard", "first edition holographic charizard"]

def main():
    with open('./secret_plan.txt', 'a') as fObj:
        fObj.write(f"Step 3. Use dollerz to buy {random.choice(OPTS)}\n")
        fObj.write(f"Step 4. Do laundry\n")
main()
