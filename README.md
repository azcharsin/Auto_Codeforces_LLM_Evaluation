# Auto_Codeforces_LLM_Evaluation
自动化爬取codeforces比赛信息和选手信息，并调用LLM(或者用于自动化提交)进行评测

## dataset_com
用于获取比赛题目信息与过往选手的rating信息

## cf_getck
用于自动化注册或登录codeforces账号，并获取cookie和cfsr_token用于后续身份认证

## contest_test
进行单场比赛的评测

## calc_rating
用于计算参与比赛后的rating变化

## cf_task
用于调用上述所有文件，自动化进行codeforces评测
