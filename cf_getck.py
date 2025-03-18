from DrissionPage import ChromiumPage, ChromiumOptions
from time import sleep
from loguru import logger
from lxml import etree
from tempfile import mkdtemp
from shutil import rmtree
from json import loads

account_info = {'handle': 'lnjlnj', 'password': 'V8bYySJM'}

def search_recursively_shadow_root_with_iframe(ele):
    """
    递归搜索shadow-root中的iframe元素
    
    Args:
        ele: 要搜索的元素
    
    Returns:
        找到的iframe元素或None
    """
    try:
        if ele.shadow_root:
            if ele.shadow_root.child().tag == "iframe":
                return ele.shadow_root.child()
        else:
            for child in ele.children():
                result = search_recursively_shadow_root_with_iframe(child)
                if result:
                    return result
    except Exception as e:
        logger.error(f"在搜索iframe时发生错误: {e}")
    return None

def search_recursively_shadow_root_with_input(ele):
    """
    递归搜索shadow-root中的input元素
    
    Args:
        ele: 要搜索的元素
    
    Returns:
        找到的input元素或None
    """
    try:
        if ele.shadow_root:
            if ele.shadow_root.ele("tag:input"):
                return ele.shadow_root.ele("tag:input")
        else:
            for child in ele.children():
                result = search_recursively_shadow_root_with_input(child)
                if result:
                    return result
    except Exception as e:
        logger.error(f"在搜索input时发生错误: {e}")
    return None

def wait_for_page_load(tab, timeout=15):
    """
    等待页面加载完成
    
    Args:
        tab: 浏览器标签页对象
        timeout: 超时时间（秒）
    
    Returns:
        bool: 页面是否加载成功
    """
    try:
        tab.ele('x://div[@class="main-content"]/div', timeout=timeout)
        return True
    except Exception as e:
        logger.error(f"等待页面加载时发生错误: {e}")
        return False

def fill_form_and_submit(tab, account_info):
    """
    填写并提交登录表单
    
    Args:
        tab: 浏览器标签页对象
        account_info: 包含账号信息的字典
    
    Returns:
        tuple: (csrf_token, cookies, headers)
    """
    try:
        # 设置登录信息
        account_info['handle'] = 'lnjlnj'
        account_info['password'] = 'V8bYySJM'
        
        # 定位表单元素
        handle_input = tab.ele('x://input[@name="handleOrEmail"]')
        password_input = tab.ele('x://input[@name="password"]')
        remember_checkbox = tab.ele('x://input[@id="remember"]')
        submit_button = tab.ele('x://input[@class="submit"]')

        # 填写表单
        handle_input.input(account_info['handle'])
        password_input.input(account_info['password'])
        remember_checkbox.click()
        sleep(1)
        submit_button.click()
        sleep(2)

        # 获取响应和CSRF令牌
        response = tab.html
        res = etree.HTML(response)
        csrf_token = ''.join(res.xpath('//meta[@name="X-Csrf-Token"]/@content'))
        title = res.xpath('//title/text()')[0]
        logger.info(f"响应标题: {title}")
        
        used_headers = {}
        try:
            # 获取性能日志列表，返回值为json字符串列表
            logs = tab.get_performance_logs()
            for log in reversed(logs):
                msg = loads(log.get("message", "{}")).get("message", {})
                # 找到第一个 Network.requestWillBeSent 消息即可
                if msg.get("method") == "Network.requestWillBeSent":
                    used_headers = msg.get("params", {}).get("request", {}).get("headers", {})
                    break
        except Exception as e:
            logger.warning(f"无法获取请求头信息：{e}")
            used_headers = {}


        return csrf_token, tab.cookies().as_dict(), used_headers

    except Exception as e:
        logger.error(f"填写表单时发生错误: {e}")

def enter_accounts(num_accounts, account_data):
    """
    批量注册账号
    
    Args:
        num_accounts: 要注册的账号数量
        account_data: 账号数据
    
    Returns:
        tuple: (csrf_token, cookies)
    """
    count = 0
    while count < num_accounts:
        try:
            count += 1
            # 配置Chrome浏览器
            co = ChromiumOptions()
            co.incognito()  # 使用隐身模式
            # co.set_argument('--headless=new')  # 启用无头模式
            co.set_argument('--no-sandbox')  # 添加 no-sandbox 参数
            co.set_argument('--remote-debugging-port=9222')
            user_data_dir = mkdtemp()
            co.set_argument(f"--user-data-dir={user_data_dir}")
            # chrome_path = '/usr/bin/google-chrome-stable'
            # co.set_paths(browser_path=chrome_path)
            
            # 初始化浏览器
            browser = ChromiumPage(co)
            browser.clear_cache()
            tab = browser.latest_tab
            
            # 访问登录页面
            tab.get("https://mirror.codeforces.com/enter", timeout=15)
            sleep(2)
            logger.info("开始登录账号")

            # 检查页面加载
            if not wait_for_page_load(tab):
                logger.error("页面加载失败，重试中...")
                tab.close()
                continue

            # 处理验证码
            if tab.ele('x://div[@class="main-content"]/div'):
                button = None
                # 查找验证码按钮
                eles = tab.eles("tag:input")
                for ele in eles:
                    if "name" in ele.attrs.keys() and "type" in ele.attrs.keys():
                        if "turnstile" in ele.attrs["name"] and ele.attrs["type"] == "hidden":
                            button = ele.parent().shadow_root.child()("tag:body").shadow_root("tag:input")
                            break
                else:
                    # 如果没找到按钮，递归搜索
                    ele = tab.ele("tag:body")
                    iframe = search_recursively_shadow_root_with_iframe(ele)
                    if iframe:
                        button = search_recursively_shadow_root_with_input(iframe("tag:body"))
                
                if button:
                    button.click()
                else:
                    logger.error("未找到验证码按钮!")
                    tab.close()
                    continue

            sleep(2)
            
            # 点击登录链接
            a_tag = True        
            while a_tag:
                register_link = tab.eles('tag:a')
                for link in register_link:
                    if link.text == "Enter":
                        link.click()
                        a_tag = False
                        break

            sleep(2)

            # 填写登录表单并获取结果
            csrf_token, cookies, headers = fill_form_and_submit(tab, account_data)
            sleep(2)
            tab.close()
            return csrf_token, cookies, headers

        except Exception as e:
            tab.close()
            logger.error(f"注册过程中发生错误: {e}")
        finally:
            if browser:
                browser.quit()  # 关闭浏览器及对应服务
            if user_data_dir:
                rmtree(user_data_dir, ignore_errors=True)

# 运行示例
if __name__ == "__main__":
    csrf_token, cookies, headers = enter_accounts(1, account_info)
    print(csrf_token, cookies, headers)
