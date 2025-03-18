import json
from curl_cffi import requests
import re
import time
from bs4 import BeautifulSoup

# 用于获取评测所需要的数据，包括contest信息、problem信息、全体的rating信息

def judge_div_by_name(contest_name):
    """
        通过比赛名字判断比赛的div
        Args:
            contest_name: str 比赛名字
        Returns:
            div: str 比赛的div
    """
    match = re.search(r'\((.*?)\)', contest_name)
    if match:
        rank = match.group(1)
        for div in ['Div. 1 + Div. 2', 'Div. 1', 'Div. 2', 'Div. 3', 'Div. 4']:
            if div in rank:
                return div
        return None
    else:
        return None

def fetch_contest_dict(div_name,count_limit = None):
    """
        获取比赛信息
        Args:
            div_name: str 比赛的div
            count_limit: int 获取比赛的数量
        Returns:
            contest_dict: dict 比赛信息{
                "2000": {
                    "name": str 比赛名字,
                    "div": str 比赛的div,
                    "problems": list of dict 比赛的题目信息
                },
                ...
            }
    """
    div_names = ['Div. 1','Div. 1 + Div. 2','Div. 2','Div. 3','Div. 4'] if div_name == 'ALL' else div_name.split(',')
    url = "https://codeforces.com/api/contest.list?gym=false"
    response = requests.get(url)
    contest_dict = {}
    if response.status_code == 200:
        total_contests_num = 0
        bid = 0
        c_list = response.json()
        if count_limit:
            while total_contests_num < count_limit and bid < len(c_list['result']):
                contest = c_list['result'][bid]
                div_rank = judge_div_by_name(contest['name'])
                if div_rank in div_names:
                    contest_dict[str(contest['id'])] = {'name':contest['name'],'div':div_rank}
                    total_contests_num += 1
                bid += 1
        else:
            for contest in c_list['result']:
                div_rank = judge_div_by_name(contest['name'])
                if div_rank in div_names:
                    contest_dict[str(contest['id'])] = {'name':contest['name'],'div':div_rank}
                    total_contests_num += 1
                bid += 1
        print(f"Success fetch contest information. Total contests: {total_contests_num}")
    else:
        print(f"Failed to fetch contest data. Status code: {response.status_code}")
    time.sleep(2)
    return contest_dict

def fetch_contest_list(contest_dict):
    """
        获取比赛列表
        Args:
            contest_dict: dict 比赛信息
        Returns:
            contest_list: list of int 比赛列表
    """
    buf_list = list(contest_dict.keys())
    contest_list = []
    for buf in buf_list:
        contest_list.append(int(buf))
    contest_list.sort()
    return contest_list

def remove_html_tag(each):
    """
        去除html标签
        Args:
            each: bs4.element.Tag html标签
        Returns:
            strBuffer: str 去除标签后的文本
    """
    child_list = each.find_all(recursive=False)
    if len(child_list) == 0:
        return each.get_text()
    else:
        strBuffer = ''
        for child in child_list:
            strBuffer += remove_html_tag(child) + '\n'
        return strBuffer

def divTextProcess(div):
    """
        处理div标签
        Args:
            div: bs4.element.Tag div标签
        Returns:
            strBuffer: str 处理后的文本
    """
    strBuffer = ''
    
    for each in div.find_all(recursive=False):
        if each.name == 'p':
            strBuffer += each.get_text() + '\n\n'
        elif each.name == 'ul':
            for li in each.find_all('li'):
                strBuffer += "- " + li.get_text() + '\n'
        elif each.name == 'pre':
            strBuffer += "```\n" + remove_html_tag(each)[1:] + "```\n"
        elif each.name == 'center':
            for tbody in each.find_all('tbody'):
                for tr in tbody.find_all('tr'):
                    strBuffer += '| '
                    for td in tr.find_all('td'):
                        strBuffer += td.get_text() + ' | '
                    strBuffer += '\n'
        elif each.name == 'div':
            strBuffer += divTextProcess(each)
    try:
        strBuffer = strBuffer.replace('$$$','$')
    except:
        pass
    return strBuffer

def fetch_problem_content(contest_id,problem_index,tags):
    """
        获取题目信息
        Args:
            contest_id: int 比赛id
            problem_index: str 题目index
            tags: list of str 题目标签
        Returns:
            data_dict: dict 题目信息{
                "title": str 题目名字,
                "time_limit": str 时间限制,
                "memory_limit": str 内存限制,
                "description": str 题目描述,
                "input": str 输入描述,
                "output": str 输出描述,
                "interaction": str 交互描述,
                "sample_input": str 样例输入,
                "sample_output": str 样例输出,
                "note": str 注意事项
            }
    """
    url = f"https://codeforces.com/problemset/problem/{contest_id}/{problem_index}"
    
    response = requests.get(url, impersonate="chrome101")
    if response.status_code == 200:
        html = response.text
        # with open('test.html','w') as f:
        #     f.write(html)
    else:
        print(f"Failed to fetch problem content. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(html,'lxml')
    data_dict = {}
    mainContent = soup.find_all(name="div", attrs={"class" :"problem-statement"})[0]

    data_dict['title'] = mainContent.find_all(name="div", attrs={"class":"title"})[0].contents[-1]
    data_dict['time_limit'] = mainContent.find_all(name="div", attrs={"class":"time-limit"})[0].contents[-1]
    data_dict['memory_limit'] = mainContent.find_all(name="div", attrs={"class":"memory-limit"})[0].contents[-1]

    data_dict['description'] = divTextProcess(mainContent.find_all("div")[10])
    interact_num = 3
    try:
        div = mainContent.find_all(name="div", attrs={"class":"input-specification"})[0]
        data_dict['input'] = divTextProcess(div)
    except:
        data_dict['input'] = None
        interact_num -= 1
    if 'interactive' in tags:
        div = mainContent.find_all(recursive=False)[interact_num]
        data_dict['output'] = None
        data_dict['interaction'] = divTextProcess(div)
    else:
        div = mainContent.find_all(name="div", attrs={"class":"output-specification"})[0]
        data_dict['output'] = divTextProcess(div)
        data_dict['interaction'] = None
        
    # Input
    div = mainContent.find_all(name="div", attrs={"class":"input"})[0]
    data_dict['sample_input'] = divTextProcess(div)
    # Onput
    div = mainContent.find_all(name="div", attrs={"class":"output"})[0]
    data_dict['sample_output'] = divTextProcess(div)
    # note
    if(len(mainContent.find_all(name="div", attrs={"class":"note"})) > 0):
        div = mainContent.find_all(name="div", attrs={"class":"note"})[0]
        data_dict['note'] = divTextProcess(div)
    else:
        data_dict['note'] = ''
 
    # print(data_dict)
    return data_dict

def fetch_problem_dict(contest_dict):
    """
        获取题目信息
        Args:
            contest_dict: dict 比赛信息
        Returns:
            contest_dict: dict 比赛信息{
                "2000": {
                    "name": str 比赛名字,
                    "div": str 比赛的div,
                    "problems": list of dict 比赛的题目信息
                },
                ...
            }
    """
    url = f"https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    contest_list = fetch_contest_list(contest_dict)
    problem_dict = {contest:[] for contest in contest_list}

    if response.status_code == 200:
        problem_list = response.json()
        print(len(problem_list['result']['problems']))
        for problem in problem_list['result']['problems']:
            if problem['contestId'] in contest_list:
                try:
                    problem['content'] = fetch_problem_content(problem['contestId'],problem['index'],problem['tags'])
                    problem_dict[problem['contestId']].append(problem)
                    print(f"Success fetch problem {problem['contestId']}-{problem['index']}")
                except Exception as e:
                    print(f"Failed to fetch problem {problem['contestId']}-{problem['index']}. Error: {e}")
    else:
        print(f"Failed to fetch problems data. Status code: {response.status_code}")
    for contest in contest_list:
        contest_dict[str(contest)]['problems'] = problem_dict[contest]
    return contest_dict

def fetch_rating_data():
    """
        获取全体的rating信息
        Returns:
            rating_list: list of int rating信息
    """
    url = f"https://codeforces.com/ratings/page/"
    page_num = 1
    rating_list = []
    while True:
        response = requests.get(url + str(page_num) , impersonate="chrome101")
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html,'lxml')
            main_content = soup.find_all(name="div", attrs={"class":"datatable ratingsDatatable"})[0]
            table = main_content.find_all(name="table")[0]
            for tr in table.find_all(name="tr"):
                td_list = tr.find_all(name="td")
                try:
                    rating_list.append(int(td_list[3].get_text().strip()))
                except:
                    pass
            print(f"Page {page_num} fetched.Rating data: {len(rating_list)}")
            page_num += 1
        else:
            print(f"Failed to fetch rating data. Status code: {response.status_code}")
            print(f"{page_num} pages fetched.")
            break
    return rating_list

if __name__ == "__main__":
    # 获取题目信息和比赛信息
    # div_name = 'ALL'
    # contest_dict = fetch_contest_dict(div_name,100)
    # contest_list = fetch_contest_list(contest_dict)
    # contest_dict = fetch_problem_dict(contest_dict)
    # with open('contest_dict.json','w') as f:
    #     json.dump(contest_dict,f)

    rating_list = fetch_rating_data()
    with open('rating_list.json','w') as f:
        json.dump(rating_list,f)

    # print(fetch_problem_content(2049,'E',['interactive']))
