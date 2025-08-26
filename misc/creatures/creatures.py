#!/usr/bin/exec-suid --real -- /usr/bin/python -I
def main():
    dialogue = input('> ').strip()
    # Cooked attention span
    if len(dialogue) > 20:
        print("The 𝖈𝖗𝖊𝖆𝖙𝖚𝖗𝖊𝖘 can't lock-in on your yapping.")
        print("If only you had Family Guy funny moments.")
        exit(1)
    # No showers
    for c in 'shower':
        if c in dialogue.lower():
            print("SHSHSHSH...SHOWER'ER!!!!!!!!")
            exit(1)
    try:
        eval(dialogue[:20])
    except Exception:
        print('The 𝖈𝖗𝖊𝖆𝖙𝖚𝖗𝖊𝖘 are confused')
        exit(1)

if __name__ == "__main__":
    print("You wake up locked in the top floor of Zimmerman Hall.")
    print("The 𝖈𝖗𝖊𝖆𝖙𝖚𝖗𝖊𝖘 roam the wasteland. They refuse to shower.")
    print("You must convince them to let you out.")
    main()
