import time
import os
import json
import re
import random
import requests

# 智能环境配置：仅在未设置时才应用默认值
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"
    
if "XAUTHORITY" not in os.environ:
    if os.path.exists("/home/headless/.Xauthority"):
        os.environ["XAUTHORITY"] = "/home/headless/.Xauthority"

print(f"[DEBUG] Env DISPLAY: {os.environ.get('DISPLAY')}")
print(f"[DEBUG] Env XAUTHORITY: {os.environ.get('XAUTHORITY')}")

from seleniumbase import SB
from selenium.webdriver.common.action_chains import ActionChains

# ================= 配置区域 =================
PROXY_URL = os.getenv("PROXY", "socks5://127.0.0.1:1080")  # 代理
COOKIE = os.getenv("COOKIE")  # 需要注入的Cookies
TG_TOKEN = os.getenv("TG_TOKEN")  # tg通知token
TG_CHAT_ID = os.getenv("TG_CHAT_ID")  # tg通知chat_id

# 目标 URL
LOGIN_URL = "https://dash.aclclouds.com/auth/login"
CHECK_URL = "https://dash.aclclouds.com/api/client"
PROJECT_URL = "https://dash.aclclouds.com/projects"
# ===========================================

class AclcloudsRenewal:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.screenshot_dir = os.path.join(self.BASE_DIR, "artifacts")
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def log(self, msg):
        timestamp = time.strftime('%H:%M:%S')
        print(f"[{timestamp}] [INFO] {msg}", flush=True)

    def human_wait(self, min_s=6, max_s=10):
        """随机模拟人类等待时间"""
        time.sleep(random.uniform(min_s, max_s))

    def send_telegram_notify(self, message, photo_path=None):
        """发送 Telegram 通知 (带图片)"""
        if not TG_TOKEN or not TG_CHAT_ID:
            self.log("⚠️ 未配置 TG_TOKEN 或 TG_CHAT_ID，跳过推送。")
            return
        
        try:
            if photo_path and os.path.exists(photo_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                requests.post(url, data={'chat_id': TG_CHAT_ID, 'caption': message}, files={'photo': open(photo_path, 'rb')})
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={'chat_id': TG_CHAT_ID, 'text': message})
            
            self.log("✅ TG 推送已发送")
        except Exception as e:
            self.log(f"❌ TG 推送失败: {e}")

    def try_click_robot(self, sb):
        el = sb.find_element("xpath", "//*[contains(text(),'I am not a robot')]")
        rect = el.rect
        x = rect["width"]/2
        y = rect["height"]/2
        self.log(f"I am not a robot中心坐标:横向-{x},纵向-{y}")
        actions = ActionChains(sb.driver)
        actions.move_to_element_with_offset(el, x, y)
        actions.pause(1)
        actions.click()
        actions.perform()

    def try_keep_click(self, sb):
        xpath = "//*[contains(text(),'I am not a robot')]"
        if sb.is_element_present("xpath", xpath): 
            el = sb.find_element("xpath", xpath)
            rect = el.rect
            x = rect["width"]/2
            y = rect["height"]/2
            new_y = y * 4
            actions = ActionChains(sb.driver)
            actions.move_to_element_with_offset(el, x, new_y)
            actions.pause(2)
            actions.click()
            actions.perform()
            return True
        return False

    def close_modal_if_present(self, sb):
        """关闭可能阻塞页面的 Close 弹窗"""
        try:
            sb.execute_script("""
            let btns = [...document.querySelectorAll('button')];
            let closeBtn = btns.find(b => b.innerText.includes('Close'));
            if (closeBtn) closeBtn.click();
            """)
        except:
            pass

    def run(self):
        self.log("=" * 40)
        self.log("🚀 Aclclouds - 多卡片并行 Renew 流程")
        self.log("=" * 40)
        self.log("🎯 正在启动 Chrome 浏览器...")
        
        with SB(
            uc=True,            # 启用反检测模式
            test=True, 
            headed=True,        # 强制有头模式
            headless=False,     # 明确禁用 headless
            xvfb=False,         # 禁用内部虚拟显示器
            chromium_arg="--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--window-position=0,0,--start-maximized",
            proxy=PROXY_URL if PROXY_URL else None
        ) as sb:
            try:
                self.log("✅ 浏览器已启动！")
                
                # 1. IP 检测
                self.log("🌍 正在检测出口 IP...")
                try:
                    sb.open("https://api.ipify.org?format=json")
                    ip_val = json.loads(re.search(r'\{.*\}', sb.get_text("body")).group(0)).get('ip', 'Unknown')
                    parts = ip_val.split('.')
                    #self.log(f"✅ 当前出口 IP: {parts[0]}.{parts[1]}.***.{parts[-1]}")
                    self.log(f"✅ 当前出口 IP: ***")
                except:
                    self.log("⚠️ IP 检测跳过...")

                # 2. 先访问目标域名（让浏览器记住站点），再用 CDP 注入 Cookie
                self.log("🔗 访问目标站点...")
                sb.open("https://dash.aclclouds.com/auth/login")
                time.sleep(3)
                self.log("🍪 通过 CDP 注入 Cookie...")
                # 使用 CDP 直接设置 cookie，绕过 JS 限制
                sb.driver.execute_cdp_cmd("Network.setCookie", {
                    "name": "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d",
                    "value": COOKIE,
                    "domain": "dash.aclclouds.com",
                    "path": "/",
                    "httpOnly": True,
                    "secure": True,
                    "sameSite": "Lax"
                })
                self.log("✅ 注入Cookie成功")
                time.sleep(2)
                time.sleep(3)

                # 3. 进入 Project 页面
                self.log("📂 进入Project页面")
                sb.uc_open_with_reconnect(PROJECT_URL, reconnect_time=25)
                time.sleep(5)
                self.close_modal_if_present(sb)

                # 4. 获取服务器卡片总数
                cards_selector = ".projects-cards-grid .client-card"
                sb.wait_for_element_present(cards_selector, timeout=15)
                cards_count = len(sb.find_elements(cards_selector))
                self.log(f"📋 共检测到 {cards_count} 个服务器卡片，开始逐一处理...")

                # 5. 循环遍历每个卡片容器
                for idx in range(cards_count):
                    # 构建当前卡片的绝对 CSS 路径定位器
                    card_css = f".projects-cards-grid > div:nth-child({idx + 1})"
                    
                    if not sb.is_element_present(card_css):
                        continue

                    # 提取该服务器名称
                    try:
                        raw_name = sb.get_text(f"{card_css} .client-card__header-title")
                        server_name = raw_name.strip().split('\n')[0].strip()
                    except:
                        server_name = f"未知服务器_卡片{idx + 1}"

                    self.log("-" * 40)
                    #self.log(f"🔍 [{idx + 1}/{cards_count}] 正在分析服务器: 【{server_name}】")
                    self.log(f"🔍 [{idx + 1}/{cards_count}] 正在分析服务器: x")
                    # 定义可能存在的按钮选择器
                    renew_btn = f"{card_css} button:contains('Renew')"
                    reactivate_btn = f"{card_css} button:contains('Reactivate')"
                    
                    has_renew = sb.is_element_visible(renew_btn)
                    has_reactivate = sb.is_element_visible(reactivate_btn)

                    # 获取操作前的过期剩余时间或挂起状态
                    time_before = "未知"
                    if sb.is_element_visible(f"{card_css} .projects-expiry-value"):
                        time_before = sb.get_text(f"{card_css} .projects-expiry-value").strip()
                    elif sb.is_element_visible(f"{card_css} .projects-suspended-banner"):
                        time_before = sb.get_text(f"{card_css} .projects-suspended-banner").strip()

                    # 如果既没有 Renew 也没有 Reactivate 按钮，说明当前不需要处理
                    if not (has_renew or has_reactivate):
                        #self.log(f"ℹ️ 服务器 【{server_name}】 当前处于安全期，无需操作。状态: {time_before}")
                        self.log(f"ℹ️ 服务器x 当前处于安全期，无需操作。状态: {time_before}")
                        self.send_telegram_notify(f"ℹ️ Aclclouds 状态汇报\n🖥️ 服务器：{server_name}\n🕒 当前状态：{time_before}\n💡 提示：未触发续期窗口，无需处理。")
                        continue

                    # 确定操作目标与动作描述
                    target_btn = renew_btn if has_renew else reactivate_btn
                    action_title = "自动续期 (Renew)" if has_renew else "重新激活 (Reactivate)"
                    
                    self.log(f"⚡ 发现可用动作 [{action_title}]，当前状态: {time_before}。开始触发...")
                    sb.scroll_to(target_btn)
                    time.sleep(2)
                    sb.click(target_btn)
                    time.sleep(3)

                    # 执行人机验证绕过逻辑
                    try:
                        self.try_click_robot(sb)
                        time.sleep(3)
                    except Exception as e:
                        self.log(f"⚠️ 触发人机验证初始点击失败或界面无拦截: {e}")

                    # 持续点击破解机制
                    self.log("🖱️ 开始进入重试循环点击...")
                    for k in range(20):
                        clicked = self.try_keep_click(sb)
                        if clicked:
                            self.log(f"  -> 第 {k + 1} 次下探尝试点击验证区")
                        time.sleep(3)
                        # 检测到任意成功关键字或人机确认层消失即可认为提交成功
                        if sb.is_element_visible("text=successfully") or not sb.is_element_visible("text=Anti-bot"):
                            self.log(f"✅ 【{server_name}】 验证层穿透成功！")
                            break

                    # 操作完一个卡片后，由于 DOM 状态被破坏，必须刷新页面重新对齐状态
                    self.log(f"🔄 刷新控制台以重置上下文，并核对 【{server_name}】 的最终状态...")
                    sb.uc_open_with_reconnect(PROJECT_URL, reconnect_time=25)
                    time.sleep(5)
                    self.close_modal_if_present(sb)

                    # 核对操作后的全新期限
                    time_after = "未获取到新时限（可能正在重置）"
                    if sb.is_element_visible(f"{card_css} .projects-expiry-value"):
                        time_after = sb.get_text(f"{card_css} .projects-expiry-value").strip()

                    # 留存当前服务器的处理快照并推送通知
                    screenshot_path = f"{self.screenshot_dir}/{server_name}_result.png"
                    sb.save_screenshot(screenshot_path)
                    
                    self.send_telegram_notify(
                        f"🎉 Aclclouds 自动运维任务完成\n"
                        f"🖥️ 服务器名称：{server_name}\n"
                        f"🔧 执行动作：{action_title}\n"
                        f"🕒 变更前状态：{time_before}\n"
                        f"🚀 变更后状态：{time_after}", 
                        screenshot_path
                    )

                self.log("=" * 40)
                self.log("✅ 所有卡片轮询扫描完毕！")

            except Exception as e:
                self.log(f"❌ 运行异常: {e}")
                import traceback
                traceback.print_exc()
                sb.save_screenshot(f"{self.screenshot_dir}/error.png")

if __name__ == "__main__":
    AclcloudsRenewal().run()