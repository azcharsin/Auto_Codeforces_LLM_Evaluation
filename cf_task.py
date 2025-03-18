import argparse
import json
from lm_eval.tasks.sft.codeforces.calc_rating import calc_elo_rating
from lm_eval.tasks.sft.codeforces.dataset_com import fetch_contest_dict, fetch_contest_list, fetch_problem_dict, fetch_rating_data
from lm_eval.tasks.sft.codeforces.contest_test import test_contest

def get_percentile(rating, rating_list):
    pos = -1
    for i in range(len(rating_list)):
        if rating >= rating_list[i]:
            pos = i
            break
    if pos == -1:
        return -1
    return pos / len(rating_list)


if __name__ == '__main__':
    contest_path = '/data/minimax-dialogue/users/chamouyue/work_codeforces/contest_dict.json'
    rating_path = '/data/minimax-dialogue/users/chamouyue/work_codeforces/rating_list.json'

    parser = argparse.ArgumentParser()
    parser.add_argument("--DivName", type=str, default="ALL")
    parser.add_argument("--UpdateRating", type=bool, default=False)
    parser.add_argument("--ContestNew", type=bool, default=False)
    parser.add_argument("--ContestNum", type=int, default=100)
    parser.add_argument("--Lang", type=str, default='cpp')
    args = parser.parse_args()
    
    # 数据处理
    div_name = args.DivName
    contest_num = args.ContestNum
    programType = args.Lang
    if args.UpdateRating:
        print("About 0.5 hour. Update rating...")
        rating_list = fetch_rating_data()
        with open(rating_path,'w') as f:
            json.dump(rating_list,f)
    else:
        with open(rating_path,'r') as f:
            rating_list = json.load(f)
        print("Not update rating")
    if args.ContestNew:
        print("About 1 hour. Update contest...")
        contest_dict = fetch_contest_dict(div_name,contest_num)
        contest_list = fetch_contest_list(contest_dict)
        contest_dict = fetch_problem_dict(contest_dict)
        with open(contest_path,'w') as f:
            json.dump(contest_dict,f)
    else:
        with open(contest_path,'r') as f:
            contest_dict = json.load(f)
        contest_list = fetch_contest_list(contest_dict)
        print("Not update contest, default DivName: ALL, ContestNum: 100")

    # 开始逐个contest进行评测
    rating = 0
    test_num = 0
    for contest_id in contest_list:
        print(f"Contest ID: {contest_id}")
        if len(contest_dict[contest_id]['problems']) > 0 :
            problem_status = test_contest(contest_dict[contest_id]['problems'], programType)
            if problem_status:
                rating = calc_elo_rating(contest_id, problem_status, rating, test_num)
                test_num += 1
                print(f"New Rating: {rating}")
            else:
                print("No problem status")
        else:
            print("No problems availible")

    print(f"Final Rating: {rating}")
    print(f"Rating Percentile: {get_percentile(rating, rating_list)}")
    print(f"Tested Contest Number: {test_num}")
