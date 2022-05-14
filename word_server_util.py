import os.path
incorrectList = []
correctList = []
# Yes I know this is very ugly, I'm just also very lazy <3

if os.path.isfile("incorrect.json"):
    with open('incorrect.json', 'r') as f:
        incorrectList = [i.strip("\n") for i in f.readlines()]

if os.path.isfile("correct.json"):
    with open('correct.json', 'r') as f:
        correctList = [i.strip("\n") for i in f.readlines()]

with open('words.txt', 'r') as f:
    wordList = [i.strip("\n") for i in f.readlines()]


for i in incorrectList:
    if i in wordList:
        wordList.remove(i)

for i in correctList:
    if i in wordList:
        wordList.remove(i)


def generate_word(key, needed_letters):
    try:
        copy = wordList.copy()
        acceptable = []

        for word in copy:
            if key == word:
                wordList.remove(word)
            elif key in word:
                acceptable.append(word)

        sortedList = sorted(acceptable, key=len, reverse=True)
        final = []
        for i in sortedList:
            count = 0
            for x in needed_letters:
                if x in i:
                    count += 1
            final.append((count, i))
        sortedList = sorted(final, reverse=True)
        word = sortedList[len(sortedList)//2][1]
        wordList.remove(word)
        if len(sortedList) > 1:
            return word
        else:
            return None
    except IndexError:
        return
