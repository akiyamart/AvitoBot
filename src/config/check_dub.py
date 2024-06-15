import json

def add_json(id, content):
    with open('db_dub.json', 'r', encoding='utf-8') as read_file:
        data = json.load(read_file)
        if data.get(str(id)) == None: 
            with open('db_dub.json', 'w', encoding='utf-8') as write_file:
                data_to_load = {
                    str(id): [
                        { 
                        "content": content 
                        }
                    ]
                    } 
                data.update(data_to_load)
                json.dump(data, fp=write_file, ensure_ascii=False, indent=2)
        else:
            with open('db_dub.json', 'w', encoding='utf-8') as write_file:
                data[str(id)].append({
                    "content": content
                })
                json.dump(data, fp=write_file, ensure_ascii=False, indent=2)


def read_json(id): 
   with open('db_dub.json', 'r', encoding='utf-8') as read_file:
       data = json.load(read_file)
       if data.get(str(id)) == None:
           return []
       return data[str(id)]

def clear_json(id): 
    with open('db_dub.json', 'r', encoding='utf-8') as read_file:
        data = json.load(read_file)
        if data.get(str(id)) != None: 
            data[str(id)] = []
            with open('db_dub.json', 'w', encoding='utf-8') as write_file:
                json.dump(data, fp=write_file, ensure_ascii=False, indent=2)
                return True