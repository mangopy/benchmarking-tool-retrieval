import os
import json
import pickle
import multiprocessing
from tqdm import tqdm

def mean(li,r=4):
    return round((sum(li))/(len(li)+0.0001),r)

def multi_load_jsonl(filename,num_processes=5):
    """

    :param filename: the jsonl file with big size
    :param num_processes:
    :return:
    """
    with open(filename,'r',encoding='utf-8') as f:
        data=[line.strip() for line in f]
        if len(data)<=20000:

            _,data=load_jsonl(0,data)
            return data
    multiprocessing.freeze_support()
    length = len(data) // num_processes + 1
    pool=multiprocessing.Pool(processes=num_processes)
    collects=[]
    for ids in range(num_processes):
        collect = data[ids * length:(ids + 1) * length]
        collects.append(pool.apply_async(load_jsonl,(ids,collect)))

    pool.close()
    pool.join()
    results=[]
    for i,result in enumerate(collects):
        ids,res=result.get()
        assert ids==i
        results.extend(res)
    # print(f"*************************** total {len(results)}  examples ****************************")
    return results

def load_jsonl(ids,data):
    data=[json.loads(line) for line in (data)]
    return ids,data

def write_file(data,filename,num_processes=20,default_name='train',indent=4):
    # print(f"************************** begin to write data to {filename} *******************************")
    if filename.endswith('.json'):
        json.dump(data,open(filename,'w'),indent=indent,ensure_ascii=False)
    elif filename.endswith('.jsonl') :
        with open(filename, 'w') as f:
            for line in data:
                f.write(json.dumps(line,ensure_ascii=False) + '\n')
    elif filename.endswith('.txt'):
        with open(filename, 'w') as f:
            for line in data:
                f.write(str(line) + '\n')
    elif filename.endswith('.pkl'):
        pickle.dump(data,open(filename,'w'))
    elif '.' not in filename:
        multi_write_jsonl(data,filename,num_processes=num_processes,default_name=default_name)
    else:
        raise "no suitable function to write data"
    print(f"************************** totally {len(data)} writing data to {filename} *******************************")

def write_jsonl(data,filename,ids=None):
    with open(filename,'w') as f:
        for line in tqdm(data):
            f.write(json.dumps(line)+'\n')
    return ids,len(data)

def multi_write_jsonl(data,folder,num_processes=10,default_name='train'):
    """

    :param filename:
    :param num_processes:
    :return:
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    length = len(data) // num_processes + 1
    pool=multiprocessing.Pool(processes=num_processes)
    collects=[]
    for ids in range(num_processes):
        filename=os.path.join(folder,f"{default_name}{ids}.jsonl")
        collect = data[ids * length:(ids + 1) * length]
        collects.append(pool.apply_async(write_jsonl,(collect,filename,ids)))

    pool.close()
    pool.join()
    cnt=0
    for i,result in enumerate(collects):
        ids,num=result.get()
        assert ids==i
        cnt+=num
    print(f"** total {cnt}  examples have been writen to {folder} **")
    return cnt

def load_file(filename,num_processes=10):
    # print(f"************************** begin to load data of {filename} *******************************")
    if filename.endswith('.jsonl'):
        return multi_load_jsonl(filename,num_processes)
    elif filename.endswith('.json'):
        return json.load(open(filename,'r'))
    elif filename.endswith('.pkl'):
        return pickle.load(filename)
    elif filename.endswith('.txt'):
        with open(filename,'r') as f:
            data=[line.strip() for line in f]
            return data
    else:
        raise "no suitable function to load data"


def fix_json_error(data: str, return_str=True):
    data = data.strip().strip('"').strip(",").strip("`")
    try:
        json.loads(data)
        return data
    except json.decoder.JSONDecodeError:
        data = data.split("\n")
        data = [line.strip() for line in data]
        for i in range(len(data)):
            line = data[i]
            if line in ['[', ']', '{', '}']:
                continue
            if line.endswith(('[', ']', '{', '}')):
                continue
            if not line.endswith(',') and data[i + 1] not in [']', '}', '],', '},']:
                data[i] += ','
            if data[i + 1] in [']', '}', '],', '},'] and line.endswith(','):
                data[i] = line[:-1]
        data = " ".join(data)

        if not return_str:
            data = json.loads(data)
        return data

