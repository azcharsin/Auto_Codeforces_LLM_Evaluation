import json
from curl_cffi import requests
import re
import time
from bs4 import BeautifulSoup
import random

import os
os.environ['CURL_CFFI_VERBOSE'] = '1'


def get_model_code_res(programType, problem_content,error_content=''):
    """
        Args:
            programType: str, 编程语言
            problem_content: dict, {
                "title": str 题目名称, 
                "time_limit": str 时间限制, 
                "memory_limit": str 内存限制, 
                "description": str 题目描述,
                "input": str 输入描述，部分题目没有这个部分
                "output": str 输出描述，部分题目没有这个部分
                "interaction": str 交互描述，部分题目没有这个部分
                "sample_input": str 样例输入
                "sample_output": str 样例输出
                "note": str 样例说明，部分题目没有这个部分         
            }
            error_content: str, error content，没有时为空
        Returns:
            code: str, the model code
    """
    rules = """
        1.The full program should be contained in a single file.
        2.If the problem statement doesn't specify the names of input or output, you must read the data from the standard input and write it to the standard output.
        3.You are forbidden to work with the Net.
        4.You are forbidden to perform input-output operations except for opening, closing, reading and writing files and standard streams given in the problem statements to perform input-output.
        5.You are forbidden to run other programs and create processes.
        6.You are forbidden to modify files or directories' permissions in the file system.
        7.You are forbidden to work with directories other than the current one.
        8.You are forbidden to work with the operating system registry.
        9.You are forbidden to create and use GUI elements (windows, dialogs etc.)
        10.You are forbidden to work with external devices.
        11.You are forbidden to perform any other actions that can in any manner destabilize the judging process.
        """
    code = "abcde"
    system_prompt = "```"
    user_prompt = "```"
    return code

def post_code_res(csrf_token, cookies, data):
    """
        Args:
            csrf_token: str, csrf token
            cookies: dict, cookies
            data: dict, post data,{
                "csrf_token": 与csrf_token参数一致, 
                "action": "submitSolutionFormSubmitted", 
                "submittedProblemCode": 对应的题目ID, 
                "programTypeId": 语言ID, 
                "source": 提交的源码, 
                "tabSize": 4, 
                "sourceFile": "",
            }
        Returns:
            submit_result: dict, submit result, codeforces网站返回的题目提交结果，字段不确定
    """
    url = 'https://codeforces.com/problemset/submit?csrf_token=' + csrf_token
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9",
        "cache-control": "max-age=0",
        "content-type": "application/x-www-form-urlencoded",
        "priority": "u=0, i",
        "upgrade-insecure-requests": "1",
        "origin": "https://codeforces.com",
        "referer": "https://codeforces.com/problemset/submit",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.98 Safari/537.36",
    }

    response = requests.post(url, headers=headers, cookies=cookies, data=data)

    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text,"html.parser")
            print("Submit successfully.")
        
            datatable = soup.find('div',{'class':'datatable'})
            table = datatable.find('table')
            submission_id = table.find_all('tr')[1]['data-submission-id']
            print("Submission_id:", submission_id)
            
            while True:
                time.sleep(5)
                url_result = 'https://codeforces.com/data/submitSource'
                headers_result = {
                    "accept": "application/json, text/javascript, */*; q=0.01",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "priority": "u=1, i",
                    "referer": "https://codeforces.com/problemset/status?my=on",
                    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.98 Safari/537.36",
                    "x-csrf-token": csrf_token,
                    "x-requested-with": "XMLHttpRequest"
                }
                data_result = {
                    "submissionId": submission_id,
                    "csrf_token": csrf_token
                }
                response = requests.post(url=url_result,headers=headers_result,cookies=cookies,data=data_result)
                submit_result = json.loads(response.text)
                if submit_result["waiting"] == "false":
                    break
            print("Submit Result:", submit_result)
            return submit_result
        except:
            print("Failed to submit solution.")
            print("1.Can't submit the same code on the same problem.")
            print("2.Check out your network.")
            print("3.Check out your account.")
            return None
    else:
        print(f"Failed to submit solution. Status code: {response.status_code}")
        return None

def get_account(retry_times = 10):
    """
        Args:
             retry_times: int, retry times
        Returns:
             csrf_token: str, csrf token
             cookies: dict, cookies
    """
    codeforces_account_path = '/data/minimax-dialogue/users/chamouyue/work_codeforces/codeforces_5s_account.txt'
    with open(codeforces_account_path, "r") as f:
        account = f.read().split("\n")

    print("Account Number:",len(account))

        
    while retry_times > 0:
        print("Retry Times:", retry_times)
        try:
            acc_id = random.randint(0,len(account)-1)
            print("Account ID:", acc_id)
            cookies = json.loads(account[acc_id])
            csrf_token = cookies["csrf_token"]
            
            data = {
                "csrf_token": csrf_token,
                "action": "submitSolutionFormSubmitted",
                "submittedProblemCode": "566C",
                "programTypeId": "91",
                "source": "this is a test" + str(random.randint(0,10000)),
                "tabSize": "4",
                "sourceFile": "",
            }
            if post_code_res(csrf_token, cookies, data):
                return csrf_token, cookies
            else:
                retry_times -= 1
        except:
            retry_times -= 1
    return None

def test_solution(csrf_token, cookies, problem_dict, programType, test_num = 8):
    """
        Args:
            csrf_token: str, csrf token
            cookies: dict, cookies
            problem_dict: dict, {
                "contestId": int 题目对应的contest ID,
                "index": str 题目对应的index,
                "name": str 题目名称,
                "type": str 题目类型, 
                "points": float 题目原始分数, 
                "tags": list of str 题目标签, 
                "content": dict, 
            }
            programType: str, 编程语言
            test_num: int, 测试次数
        Returns:
            solve_result: list 单道题目的测试结果如["WA", "CE", "WA", "AC"]
    """
    problem_id = str(problem_dict['contestId']) + problem_dict['index']
    lang_map = {
        'kotlin': 88,  # Kotlin 1.9.21
        'cpp': 91,     # GNU G++23 14.2 (64 bit, msys2)
        'ruby': 67,    # Ruby 3.2.2
        'd': 28,       # D DMD32 v2.105.0
        'python': 70,  # PyPy 3.10 (7.3.15, 64bit)
        'pascal': 51,  # PascalABC.NET 3.8.3
        'rust': 75,    # Rust 1.75.0 (2021)
        'go': 32,      # Go 1.22.2
        'node.js': 55, # Node.js 15.8.0 (64bit)
        'haskell': 12, # Haskell GHC 8.10.1
        'javascript': 34, # JavaScript V8 4.8.0
        'csharp': 79,  # C# 10, .NET SDK 6.0
        'perl': 13,    # Perl 5.20.1
        'java': 87,    # Java 21 64bit
        'ocaml': 19,   # OCaml 4.02.1
        'delphi': 3,   # Delphi 7
        'php': 6,      # PHP 8.1.7
        'scala': 20,   # Scala 2.12.8
        'c': 43        # GNU GCC C11 5.1.0
    }
    status_dict = {
        'Memory limit exceeded':'MLE',
        'Time limit exceeded':'TLE',
        'Runtime error':'RE',
        'Compilation error':'CE',
        'Wrong answer':'WA',
        'Accepted':'AC',
        'Idleness limit exceeded':'ILE',
        'Denial of judgement':'DOJ',
    }
    error_dict = {
        'MLE':'The program tries to consume more memory than is indicated in the problem statement.',
        'TLE':'The program hadn\'t terminated in time indicated in the problem statement.',
        'RE':'The program terminated with a non-zero return code (possible reasons: array out of bound error, division by zero, stack overflow, incorrect pointers usage, etc).',
        'CE':'The program hadn\'t compiled.',
        'WA':'The program produced an incorrect answer.',
        'ILE':'The program didn\'t use the CPU time for considerable time.',
        'DOJ':'The solution was impossible to run, perhaps, due to a judging error. The most probable cause is an error in the program (for example, using extra large arrays).',
    }
    programTypeId = lang_map[programType]
    solve_result = []
    success_num = 0
    for _ in range(test_num):
        error_content = ''
        print(f"Problem Test {_+1} on {problem_id}:")
        data = {
            "csrf_token": csrf_token,
            "action": "submitSolutionFormSubmitted",
            "submittedProblemCode": problem_id,
            "programTypeId": str(programTypeId),
            "source": get_model_code_res(programType,problem_dict['content'],error_content),
            "tabSize": "4",
            "sourceFile": "",
        }
        submit_result = post_code_res(csrf_token, cookies, data)
        if submit_result:
            success_num += 1
            print(f"-----------\nSubmit successfully.")
            verdict = "Unknown"
            for status_key in list(status_dict.keys()):
                if status_key in submit_result:
                    verdict = status_dict[status_key]
                    break
            print(f"Status: {verdict}")
            solve_result.append(verdict)

            if verdict == "AC":
                return solve_result
            else:
                testCount = int(submit_result["testCount"])
                error_content = f"{verdict}: {error_dict[verdict]}\nTotal test: {testCount}\n"
                for i in range(testCount):
                    error_content += f"Test {i+1}: time: {submit_result[f'timeConsumed#{i+1}']} ms, memory: {submit_result[f'memoryConsumed#{i+1}']} KB, exit code: {submit_result[f'exitCode#{i+1}']}, checker exit code :{submit_result[f'checkerExitCode#{i+1}']}, verdict :{submit_result[f'verdict#{i+1}']}\n"
                    try:
                        error_content += f"Input:\n{submit_result[f'input#{i+1}']}\n"
                    except:
                        pass
                    try:
                        error_content += f"Output:\n{submit_result[f'output#{i+1}']}\n"
                    except:
                        pass
                    try:
                        error_content += f"Answer:\n{submit_result[f'answer#{i+1}']}\n"
                    except:
                        pass
                    error_content += f"checker log:\n{submit_result[f'checkerStdoutAndStderr#{i+1}']}\n"
                    try:
                        error_content += f"diagnostics:\n{submit_result[f'diagnostics#{i+1}']}\n"
                    except:
                        pass
                    try:
                        error_content += f"winnt Status:\n{submit_result[f'winntStatus#{i+1}']}\n"
                    except:
                        pass
                    try:
                        error_content += f"Accepted:\n{submit_result[f'accepted#{i+1}']}\n"
                    except:
                        pass
                    
        else:
            print(f"----------\nFailed to submit solution.")

    print(f"Success Test: {success_num}/8")
    return solve_result

def test_contest(problem_list, programType):
    """
        Args:
            problem_list: list of dict
            programType: str, 编程语言
        Returns:
            test_result: dict, 测试结果，如{"A":["AC","WA","CE","WA"],"B":["AC","WA","WA","WA"]}    
    """
    test_result = {}
    try:
        csrf_token, cookies = get_account(10)
        print("Successfully get account.")
    except:
        print("Failed to get account.")
        return None
    for problem_dict in problem_list:
        solve_result = test_solution(csrf_token, cookies, problem_dict, programType)
        final_result = [s for s in solve_result if s != "CE" and s != "DOJ"]
        test_result[problem_dict['index']] = final_result
    return test_result
        

if __name__ == "__main__":
    # sel_test()
    # req_test()
    # problem_dict = {"contestId": 1941, "index": "G", "name": "\u0420\u0443\u0434\u043e\u043b\u044c\u0444 \u0438 \u043c\u0435\u0442\u0440\u043e", "type": "PROGRAMMING", "rating": 2000, "tags": ["constructive algorithms", "dfs and similar", "graphs", "shortest paths"], "content": {"title": "G. Rudolf and Subway", "time_limit": "2 seconds", "memory_limit": "256 megabytes", "description": "Building bridges did not help Bernard, and he continued to be late everywhere. Then Rudolf decided to teach him how to use the subway.\n\nRudolf depicted the subway map as an undirected connected graph, without self-loops, where the vertices represent stations. There is at most one edge between any pair of vertices.\n\nTwo vertices are connected by an edge if it is possible to travel directly between the corresponding stations, bypassing other stations. The subway in the city where Rudolf and Bernard live has a color notation. This means that any edge between stations has a specific color. Edges of a specific color together form a subway line. A subway line cannot contain unconnected edges and forms a connected subgraph of the given subway graph.\n\nAn example of the subway map is shown in the figure.\n\nRudolf claims that the route will be optimal if it passes through the minimum number of subway lines.\n\nHelp Bernard determine this minimum number for the given departure and destination stations.\n\n", "input": "The first line contains an integer $t$ ($1 \\le t \\le 10^4$)\u00a0\u2014 the number of test cases.\n\nThis is followed by descriptions of the test cases.\n\nThe first line of each test case contains two integers $n$ and $m$ ($2 \\le n \\le 2 \\cdot 10^5, 1 \\le m \\le 2 \\cdot 10^5$) \u2014 the number of subway stations and the number of direct routes between stations (i.e., graph edges).\n\nThis is followed by $m$ lines \u2014 the description of the edges. Each line of the description contains three integers $u$, $v$, and $c$ ($1 \\le u, v \\le n, u \\ne v, 1 \\le c \\le 2 \\cdot 10^5$) \u2014 the numbers of the vertices between which there is an edge, and the color of this edge. It is guaranteed that edges of the same color form a connected subgraph of the given subway graph. There is at most one edge between a pair of any two vertices.\n\nThis is followed by two integers $b$ and $e$ ($1 \\le b, e \\le n$) \u2014 the departure and destination stations.\n\nThe sum of all $n$ over all test cases does not exceed $2 \\cdot 10^5$. The sum of all $m$ over all test cases does not exceed $2 \\cdot 10^5$.\n\n", "output": "For each testcase, output a single integer \u2014 the minimum number of subway lines through which the route from station $b$ to station $e$ can pass.\n\n", "interaction": None, "sample_input": "```\n\n6 6\n1 2 1\n2 3 1\n5 2 2\n2 4 2\n4 6 2\n3 6 3\n1 3\n6 6\n1 2 1\n2 3 1\n5 2 2\n2 4 2\n4 6 2\n3 6 3\n1 6\n6 6\n1 2 1\n2 3 1\n5 2 2\n2 4 2\n4 6 2\n3 6 3\n6 6\n4 3\n1 2 1\n1 3 1\n4 1 1\n2 3\n6 7\n1 2 43\n1 3 34\n4 6 43\n6 3 43\n2 3 43\n5 3 43\n4 5 43\n1 6\n```\n", "sample_output": "```\n1\n2\n0\n1\n1\n```\n", "note": "The subway graph for the first example is shown in the figure in the problem statement.\n\nIn the first test case, from vertex $1$ to vertex $3$, you can travel along the path $1 \\rightarrow 2 \\rightarrow 3$, using only the green line.\n\nIn the second test case, from vertex $1$ to vertex $6$, you can travel along the path $1 \\rightarrow 2 \\rightarrow 3 \\rightarrow 6$, using the green and blue lines.\n\nIn the third test case, there is no need to travel from vertex $6$ to the same vertex, so the number of lines is $0$.\n\nIn the fourth test case, all edges of the graph belong to one line, so the answer is $1$.\n\n"}}
    # submit_solution(problem_dict,91,1)
    csrf_token = "61d88da55305d1a36c5a84d375536b19"
    cookies = {"_ga": "GA1.1.1297203047.1739935831", "_ga_K230KVN22K": "GS1.1.1739935830.1.1.1739935834.0.0.0", "X-User": "a30d0201c25b58695852462e06254929b82ddc3e187732d86290c9bccc776cef835913757b5b8327", "X-User-Sha1": "cac5f99710e404467e413b180f490d0c05e30a5d", "evercookie_etag": "xt7salv6986fg25od1", "70a7c28f3de": "xt7salv6986fg25od1", "evercookie_cache": "xt7salv6986fg25od1", "evercookie_png": "xt7salv6986fg25od1", "_gat_gtag_UA_743380_5": "1", "_gid": "GA1.2.1969362896.1739935831", "39ce7": "CFL9OkWc", "pow": "6db9fc5f174abf4246ab24df7b4a01bc84ea1864", "cf_clearance": "PcQpPsAoul7__VYU3_IDtvoMOr83ruGSLtk7TCQ0imc-1739935829-1.2.1.1-QJ937lC_17MmppfGBb1ilF073BPzl0Qf4Hjed2.C.dN3fU0rDrsXkM8VI3VUSmhGuSu6xyaokFJSXqhpYpe54mc9Jfw6X7wp2MEkRaPcw4LH9s97dr27lcpPGkjPSq.Cuu_V0dPn8X0kDucje0o7V36eEmjzrsRWRR7RCEWCmjsoFX8onUgZcE1q8dcbaXkI3TOEPrOdfS300OpcsvJ5sbwtHKO6CTWsRTaf4VDgtsrrsN3mlr1xkNmDkDtuQu3VznjOtyoxhEyGs38cR6ZaBXaSIBsbj894i_QeXuogzvab_3NPtENDqpHxIs3fufv43yZ4q5cxt3BLFwc_AwxgRw", "JSESSIONID": "916AEE31CCDC4C2A671CB0C39ABB78AB", "csrf_token": "61d88da55305d1a36c5a84d375536b19"}
    data = {
        "csrf_token": csrf_token,
        "action": "submitSolutionFormSubmitted",
        "submittedProblemCode": "2066A",
        "programTypeId": "91",
        "source": "aabbcc",
        "tabSize": "4",
        "sourceFile": "",
    }
    post_code_res(csrf_token, cookies, data)
