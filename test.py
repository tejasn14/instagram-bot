# print('12.9'.isnumeric())
# print('12.9k'.isnumeric())

# print('asdf{}asdf'.format(123))


import json

with open('./comments.json', 'r', encoding="utf8") as filehandle:
    basicList = json.load(filehandle)
print(basicList)
