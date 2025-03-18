import requests

###
# 用于计算Codeforces的Elo Rating的变化
###
def calc_elo_rating(contest_id, problem_status, old_rating, confined_num = None): # confined_num:from 0 to 5
    """
        计算Codeforces的Elo Rating的变化
        Args:
            contest_id: int 比赛ID
            problem_status: list of str 每个题目的提交状态
            old_rating: int 旧的Rating
            confined_num: int 第n场定级赛，从0-5，None表示不是定级赛
        Returns:
            new_rating: 新的Rating
    """
    print(f"Calculating rating for contest_id: {contest_id}")

    try:
        standings = requests.get(f"https://codeforces.com/api/contest.standings?contestId={contest_id}&showUnofficial=false").json()
        rating_changes = requests.get(f"https://codeforces.com/api/contest.ratingChanges?contestId={contest_id}").json()
        handle_set = set([standings["result"]["rows"][i]["party"]["members"][0]["handle"] for i in range(len(standings["result"]["rows"]))]) and \
            set([rating_changes["result"][i]["handle"] for i in range(len(rating_changes["result"]))])
        standings["result"]["rows"] = [standings["result"]["rows"][i] for i in range(len(standings["result"]["rows"])) if standings["result"]["rows"][i]["party"]["members"][0]["handle"] in handle_set]
        rating_changes["result"] = [rating_changes["result"][i] for i in range(len(rating_changes["result"])) if rating_changes["result"][i]["handle"] in handle_set]
        assert len(standings["result"]["rows"]) == len(rating_changes["result"]) and len(standings["result"]["rows"]) > 200
        print(f"Number of handle: {len(handle_set)}")
    except Exception as e:
        print(e)

    if "result" not in standings or "result" not in rating_changes or len(standings["result"]["rows"]) != len(rating_changes["result"]) or len(standings["result"]["rows"]) <= 200:
        print("No result")
        return
    max_rating = 0
    for i in range(len(rating_changes["result"])):
        max_rating = max(max_rating, rating_changes["result"][i]["oldRating"])
    score = 0
    penalty = 0
    
    for problem in standings["result"]["problems"]:
        prob = f"{problem['index']}"
        if prob in problem_status.keys():
            for ith, status in enumerate(problem_status[prob]):
                if status == "AC":
                    print(f"AC at {prob} in {ith + 1}th submission, total submissions: {len(problem_status[prob])}")
                    if "points" in problem:
                        score += max(problem["points"] * 0.3, problem["points"] - 50 * ith)
                    else:
                        score += 1
                        penalty += ith * 10
                    break
                
    print(f"Score: {score}, Penalty: {penalty}")

    n = len(standings["result"]["rows"])
    rank = n
    for i in range(n):
        if standings["result"]["rows"][i]["points"] < score or (standings["result"]["rows"][i]["points"] == score and standings["result"]["rows"][i]["penalty"] > penalty):
            rank = i
            break
    print(f"Rank: {rank}")

    l, r = 0, max_rating + 100
    while r - l > 1:
        mid = int((l + r) / 2)
        new_seed = 1
        for i in range(n):
            new_seed += 1 / (1 + 10 ** ((mid - rating_changes["result"][i]["oldRating"]) / 400))
        if new_seed < rank:
            r = mid
        else:
            l = mid
    if confined_num < 6:
        score_list = [500,350,250,150,100,50]
        for i in range(confined_num):
            old_rating -= score_list[i]
        old_rating += 1400
        print(f"Rating: {l}")
        d_rating = (l - old_rating)//2
        new_rating = old_rating + d_rating + score_list[confined_num]
        print(f"New rating: {new_rating}")
        return new_rating
    else:
        print(f"Rating: {l}")
        new_rating = (l + old_rating)//2
        print(f"New rating: {new_rating}")
        return new_rating


if __name__ == "__main__":
    rating = calc_elo_rating(2024, {"A": ["WA", "AC"], "B": ["AC", "WA"]},2000)
    # print(f"rating: {rating}")
    # calc_elo_rating(2024, {"A": ["AC", "AC"], "B": ["AC", "WA"]})
    # calc_elo_rating(2032, {"A": ["AC", "AC"], "B": ["AC", "WA"]})
