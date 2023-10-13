import winreg
import asyncio
from datetime import datetime, timedelta

import pypinyin as pyin
import pandas as pd
from playwright.async_api import async_playwright, Page

from Autoseek.settings import CONFIG
from .model import Record, Schedule


def get_sys_chrome() -> str:
    '''获取系统Chrome路径'''
    try:
        key = winreg.HKEY_LOCAL_MACHINE
        subkey = r"SOFTWARE\Clients\StartMenuInternet\Google Chrome\DefaultIcon"
        chromekey = winreg.OpenKey(key, subkey)
    except FileNotFoundError:
        key = winreg.HKEY_CURRENT_USER
        subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
        chromekey = winreg.OpenKey(key, subkey)
    path, _ = winreg.QueryValueEx(chromekey, "")
    return path


def eng_name(name: str) -> str:
    '''获取姓名字母缩写'''
    return "".join(pyin.lazy_pinyin(name, style=pyin.Style.FIRST_LETTER)).upper()


def next_month_day(today: str):
    '''获取下月当天'''
    _today = datetime.strptime(today, "%Y%m%d")
    nextmonth = _today + timedelta(days=30)
    return nextmonth.strftime("%Y-%m-%d")


async def parse_excel(filename: str) -> tuple[list[Record], list[Schedule]]:
    '''解析Excel'''
    df = await asyncio.to_thread(pd.read_excel, filename)
    date_list = list(set(df["纯化时间"]))
    record_list, sheudle_list = [], []
    for today in date_list:
        _today = datetime.strptime(today, "%Y-%m-%d")
        subdata = df[df["纯化时间"] == today]
        # 生成记录
        _, exist_record = Record.get_or_none(date=_today)
        if not exist_record:
            record_list.append(Record.from_dataframe(subdata))

        # 生成日程
        # _, exist_shedule = Shedule.get_or_none(date=_today)
        # if not exist_shedule:
        #     sheudle_list.append(Shedule.from_dataframe(subdata))
    return record_list, sheudle_list


async def writeRecord(page: Page, record: Record):
    '''填写实验记录'''
    config = CONFIG["SCHEDULE"]
    await page.wait_for_load_state("networkidle")
    # 实验成功
    await page.locator("//div[text()='结论']/.. >> //span[text()='请选择']").click()
    await page.click("text=成功")
    # 关键词
    keywords = record.projects
    await page.fill("textarea[placeholder='一百字以内']", ",".join(keywords))
    # 填写实验人，实验日期
    await page.fill("//*[text()='实验人员']/../.. >> input", config["name"])
    await page.fill("//*[text()='实验日期']/../.. >> input", record.date.strftime("%Y.%m.%d"))
    # 柱子批号
    await page.wait_for_selector("div.component-title:has-text('耗材') >> .. >> tr.ivu-table-row", state="attached")
    consumable = page.locator(
        "div.component-title:has-text('耗材') >> .. >> tr.ivu-table-row")
    if record.protocol == "Protein A重力柱亲和层析操作流程":
        await consumable.nth(0).locator("//td[3]").click()
        await consumable.nth(0).locator("//td[3] >> input").fill(config["pa"])
    elif record.protocol == "Protein A AKTA亲和层析操作流程":
        await consumable.nth(0).locator("//td[3]").click()
        await consumable.nth(0).locator("//td[3] >> input").fill(config["pa_akta"])
    elif record.protocol == "Ni2+ Smart Bead重力柱亲和层析操作流程":
        await consumable.nth(0).locator("//td[3]").click()
        await consumable.nth(0).locator("//td[3] >> input").fill(config["ni"])
    elif record.protocol == "Ni2+ Smart Beads AKTA亲和层析操作流程":
        await consumable.nth(0).locator("//td[3]").click()
        await consumable.nth(0).locator("//td[3] >> input").fill(config["ni_akta"])
    await page.click("div.component-title:has-text('耗材')")
    await page.mouse.wheel(0, 1000)
    await page.wait_for_load_state("networkidle")
    # 填写溶液种类、批号、保质期
    await page.wait_for_selector("div.component-title:has-text('溶液配制') >> .. >> tr.ivu-table-row", state="attached")
    buffer_list = page.locator(
        "div.component-title:has-text('溶液配制') >> .. >> tr.ivu-table-row")
    weeknum = record.date.strftime("%Y-%W")
    if weeknum[-2:] == "00":
        weeknum = (record.date-timedelta(days=6)).strftime("%Y-%W")
    buffer_batch = self.buffers[weeknum]       # 常规buffer批号
    shelflife = next_month_day(buffer_batch[-8:])     # 保质期
    buffers = record.buffers()     # 缓冲液列表
    # 添加缓冲液
    if len(buffers) > 1:
        for i in range(len(buffers)-1):
            await page.click("div.component-title:has-text('溶液配制') >> .. >> text='新增'")
            newrow = buffer_list.nth(await buffer_list.count()-1)
            await newrow.locator("//td[2]").click()
            if record.protocol == "分子排阻色谱层析操作流程":
                await newrow.locator("//td[2] >> input").fill("Binding Buffer（"+buffers[i+1]+"）")
            elif record.protocol == "离子交换层析操作流程":
                await newrow.locator("//td[2] >> input").fill("Buffer A（"+buffers[i+1]+"）")
            else:
                await newrow.locator("//td[2] >> input").fill("置换缓冲液（"+buffers[i+1]+"）")
            await newrow.locator("//td[4]").click()
            await newrow.locator("//td[4] >> input").fill("三优生物")
            if record.protocol == "离子交换层析操作流程":
                await page.click("div.component-title:has-text('溶液配制') >> .. >> text='新增'")
                extrarow = buffer_list.nth(await buffer_list.count()-1)
                await extrarow.locator("//td[2]").click()
                elution = buffers[i+1].split(",")
                elution.insert(1, "0.5M NaCl")
                elution = ",".join(elution)
                await extrarow.locator("//td[2] >> input").fill("Buffer B（"+elution+"）")
                await extrarow.locator("//td[4]").click()
                await extrarow.locator("//td[4] >> input").fill("三优生物")
    for i in range(await buffer_list.count()):
        buffername = await buffer_list.nth(i).locator("//td[2]/div/div").text_content()
        # buffer 种类
        if record.protocol == "分子排阻色谱层析操作流程":
            if buffername == "Binding Buffer":
                await buffer_list.nth(i).locator("//td[2]").click()
                await buffer_list.nth(i).locator("//td[2] >> input").fill("Binding Buffer（"+buffers[0]+"）")
        elif record.protocol == "离子交换层析操作流程":
            if buffername == " Buffer A":
                await buffer_list.nth(i).locator("//td[2]").click()
                await buffer_list.nth(i).locator("//td[2] >> input").fill("Buffer A（"+buffers[0]+"）")
            elif buffername == "Buffer B":
                await buffer_list.nth(i).locator("//td[2]").click()
                elution = buffers[0].split(",")
                elution.insert(1, "0.5M NaCl")
                elution = ",".join(elution)
                await buffer_list.nth(i).locator("//td[2] >> input").fill("Buffer B（"+elution+"）")
        else:
            if buffername == "置换缓冲液":
                await buffer_list.nth(i).locator("//td[2]").click()
                await buffer_list.nth(i).locator("//td[2] >> input").fill("置换缓冲液（"+buffers[0]+"）")
        # 批号、保质期
        if (record.protocol == "离子交换层析操作流程") and (("Buffer A" in buffername) or ("Buffer B" in buffername)):
            await buffer_list.nth(i).locator("//td[3]").click()
            # 批号
            await buffer_list.nth(i).locator("//td[3] >> input").fill(eng_name(config["name"])+record.date.strftime("%Y%m%d"))
            await buffer_list.nth(i).locator("//td[5]").click()
            # 保质期
            await buffer_list.nth(i).locator("//td[5] >> input").fill(next_month_day(record.date.strftime("%Y%m%d")))
            await buffer_list.nth(i).locator("//td[3]").click()
        else:
            await buffer_list.nth(i).locator("//td[3]").click()
            # 批号
            await buffer_list.nth(i).locator("//td[3] >> input").fill(buffer_batch)
            await buffer_list.nth(i).locator("//td[5]").click()
            # 保质期
            await buffer_list.nth(i).locator("//td[5] >> input").fill(shelflife)
            await buffer_list.nth(i).locator("//td[3]").click()
    await page.click("div.component-title:has-text('溶液配制')")
    await page.mouse.wheel(0, 1200)
    await page.wait_for_load_state("networkidle")
    # 上传数据文件
    await page.frame_locator("text=实验结果 导入 >> iframe").locator("text=文件").click()
    await page.frame_locator("text=实验结果 导入 >> iframe").locator("//div[@title='导入']").click()
    await page.frame_locator("text=实验结果 导入 >> iframe").locator("text=Excel文件").first.click()
    async with page.expect_file_chooser() as fc_info:
        await page.frame_locator("text=实验结果 导入 >> iframe").locator("//div[@title='导入 Excel 文件']").click()
    file_chooser = await fc_info.value
    await file_chooser.set_files(record.filepath)
    # 填写实验结论
    await page.fill("div.component-title:has-text('实验结论') >> .. >> textarea", record.conclusion())
    # 填写数据路径
    await page.fill("div.component-title:has-text('数据保存路径') >> .. >> textarea", config["srcpath"])
    # 提交保存
    await page.click("p:has-text('签名提交')")
    await page.click("button:has-text('保存并提交')")
    await page.wait_for_selector("//div[text()='签名提交']", state="attached")
    submitpanel = page.locator("//div[text()='签名提交']/../.. >> visible=true")
    await submitpanel.locator("input[placeholder='请输入密码']").fill(config["record_password"])
    await submitpanel.locator("div.ivu-select-selection").click()
    teams = submitpanel.locator(
        "div.ivu-select-dropdown > ul.ivu-select-dropdown-list > li")
    for i in range(await teams.count()):
        teamname = await teams.nth(i).locator("//div").text_content()
        if (teamname == "FM1-蛋白纯化"):
            ppers = teams.nth(i).locator("//ul/li/li")
            for j in range(await ppers.count()):
                ppname = await ppers.nth(j).text_content()
                if (ppname == "王娇"):
                    await ppers.nth(j).click()
                    break
            break
    await submitpanel.locator("div.ivu-select-selection").click()
    await submitpanel.locator("button:has-text(\"提交\")").click()
    await page.wait_for_load_state("networkidle")
    # Close page
    await page.close()
    record.complete()


async def notebook(recordlist: list[Record], debug, callback):
    '''实验记录批量处理'''
    config = CONFIG["SCHEDULE"]
    if not config["chrome"]:
        raise ValueError("未找到谷歌浏览器")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=not debug,
            executable_path=config["chrome"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(60000)
        await page.goto("https://edm.ilabpower.com/")
        # 登录
        await page.fill("[placeholder='请输入手机号/邮箱']", config["record_username"])
        await page.fill("[placeholder='请输入密码']", config["record_password"])
        async with page.expect_navigation():
            await page.click("//button/*[text()='登录']")
        await page.wait_for_load_state("networkidle")
        # 打开实验数据管理模块
        async with page.expect_popup() as popup_info:
            entrance = page.locator("//div[text()='电子实验记录本']")  # 新版app入口
            if entrance is None:
                entrance = page.locator("//a[text()='实验数据管理']")  # 旧版app入口
            await entrance.click()
        page1 = await popup_info.value
        page1.set_default_timeout(60000)
        await page1.wait_for_load_state("networkidle")
        # 关闭公告页
        notice = page1.locator("//*[@id='helpModal']/../.. >> visible=true")
        if notice is not None:
            await notice.locator("a.ivu-modal-close").click()

        tasks = []
        for record in sorted(recordlist):
            # 获取buffer批号
            # weeknum = record.date.strftime("%Y-%W")
            # if weeknum[-2:] == "00":
            #     weeknum = (record.date-timedelta(days=6)).strftime("%Y-%W")
            # if weeknum not in self.buffers:
            #     self.notebookQueue.put("no buffer")
            #     continue
            await page1.click("//p[text()='新建实验']")
            await page1.wait_for_selector("//div[text()='新建实验']/../..", state="attached")
            panel = page1.locator(
                "//div[text()='新建实验']/../..")     # base panel
            # 实验标题
            experiment_title = f"{record.date.strftime('%Y%m%d')}-{record.protocol}"
            await panel.locator("[placeholder='输入标题(300字符)']").fill(experiment_title)
            # 选择模板
            await panel.locator("//label[text()='实验模板']/.. >> //input[@type='text']").click()
            protocol_list = panel.locator(
                "//label[text()='实验模板']/.. >> li.ivu-select-item")
            for i in range(await protocol_list.count()):
                protocolname = await protocol_list.nth(i).text_content()
                if protocolname[0:len(record.protocol)] == record.protocol:
                    await protocol_list.nth(i).click()
                    break
            # 选择记录本
            await panel.locator("//label[text()='记录本']/.. >> //input[@type='text']").click()
            notebook_list = panel.locator(
                "//label[text()='记录本']/.. >> li.ivu-select-item")
            for i in range(await notebook_list.count()):
                notebookname = await notebook_list.nth(i).text_content()
                notebookname = notebookname[notebookname.find("(")+1:-1]
                if notebookname == (f"蛋白纯化-{config['name']}"):
                    await notebook_list.nth(i).click()
                    break
            # await page1.goto("https://edm.ilabpower.com/project", wait_until="networkidle")
            # await page1.wait_for_timeout(1000)
            # await page1.click("text=全部")
            # 提交
            async with page1.expect_popup() as popup_info:
                # await page1.click("text=NB221862-2")
                await panel.locator("button:has-text('提交')").click()
            page2 = await popup_info.value
            page2.set_default_timeout(60000)
            task = asyncio.create_task(writeRecord(page2, record))
            task.add_done_callback(callback)
            tasks.append(task)
        await asyncio.gather(*tasks)
        # 关闭浏览器
        await context.close()
        await browser.close()


async def writeSchedule(page: Page, schedule: Schedule):
    '''填写工时'''
    notfoundlist = []
    await page.wait_for_load_state("networkidle")
    frame1 = page.frame("zwIframe")
    # 填写时间
    await frame1.fill("//div[text()='填写时间']/.. >> input[maxlength='255']",
                      schedule.opentime.strftime("%Y-%m-%d"))
    # 平台事务
    if len(schedule.projects) == 0:
        await frame1.fill("//div[text()='平台事务开始时间']/.. >> input[maxlength='255']",
                          schedule.opentime.strftime("%Y-%m-%d %H:%M"))
        await frame1.fill("//div[text()='平台事务结束时间']/.. >> input[maxlength='255']",
                          schedule.closetime.strftime("%Y-%m-%d %H:%M"))
    else:
        if schedule.opentime < schedule.projects[0].starttime:
            await frame1.fill("//div[text()='平台事务开始时间']/.. >> input[maxlength='255']",
                              schedule.opentime.strftime("%Y-%m-%d %H:%M"))
            await frame1.fill("//div[text()='平台事务结束时间']/.. >> input[maxlength='255']",
                              schedule.projects[0].starttime.strftime("%Y-%m-%d %H:%M"))
        # 项目工时
        await frame1.click(
            "//div[text()='平台']/.. >> div[class='icon CAP cap-icon-mingxibiaoxuanzeqi']")
        await page.wait_for_timeout(1000)
        await page.frame_locator("#RelationPage_main >> iframe").locator(
            "input[type='checkbox']").check()
        await page.click("text=确定")
        await frame1.wait_for_selector("//div[text()='蛋白纯化']")
        for i in range(len(schedule.projects)-1):
            async with page.expect_navigation():
                await frame1.click("text=复制")
        await frame1.wait_for_selector("//div[text()='项目号']", state="attached")
        sections = frame1.locator("//div[text()='项目号']/.. ")
        # print("section:%d"%sections.count())
        for i in range(len(schedule.projects)):
            await sections.nth(i).locator(
                "div[class='icon CAP cap-icon-mingxibiaoxuanzeqi']").click()
            # 搜索项目
            await page.wait_for_selector(
                "iframe[name='layui-layer-iframe%d']" % (2+i), state="attached")
            active_frame = page.frame_locator(
                "iframe[name='layui-layer-iframe%d']" % (2+i))
            await page.wait_for_timeout(1000)
            await active_frame.locator(
                "//em[@title='项目号']/.. >> input").fill(schedule.projects[i].name)
            await active_frame.locator("button:has-text('筛选')").click()
            await page.wait_for_timeout(500)
            search_list = active_frame.locator(
                "tr:has(input[type='checkbox'])")
            search_num = await search_list.count()
            if search_num == 0:
                await page.click("text=取消")
                notfoundlist.append(schedule.projects[i].name)
            else:
                for j in range(search_num):
                    content = await search_list.nth(j).locator(
                        "//td[3] >> span").text_content()
                    content = content.strip()
                    if schedule.projects[i].name == content:
                        await search_list.nth(j).locator(
                            "input[type='checkbox']").check()
                        await page.click("text=确定")
                        await page.wait_for_timeout(500)
                        # 填写开始结束时间
                        await frame1.locator("//div[text()='项目开始时间']/.. >> input[maxlength='255']").nth(
                            i).fill(schedule.projects[i].starttime.strftime("%Y-%m-%d %H:%M"))
                        await frame1.locator("//div[text()='项目结束时间']/.. >> input[maxlength='255']").nth(
                            i).fill(schedule.projects[i].endtime.strftime("%Y-%m-%d %H:%M"))
                        break
                    if j == search_num-1:
                        await page.click("text=取消")
                        notfoundlist.append(schedule.projects[i].name)
    # 发送
    await frame1.click("text=审批意见:")
    if not notfoundlist:
        await page.click("text=发送")
        await page.wait_for_selector("text=确定")
        schedule.complete()
    await page.close()
    return notfoundlist


async def worktime(schedulelist: list[Schedule], debug, callback):
    '''工时批量处理'''
    config = CONFIG["SCHEDULE"]
    if not config["chrome"]:
        raise ValueError("未找到谷歌浏览器")
    notfoundlist = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=not debug,
            executable_path=config["chrome"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("http://sanyoubio.gnway.vip/seeyon/")
        # 登录
        await page.fill("#login_username", config["worktime_username"])
        await page.fill("#login_password1", config["worktime_password"])
        await page.click("text=登 录")
        for schedule in sorted(schedulelist):
            schedule.dispatch()
            # 打开填报单
            await page.click("//div[text()='工时管理']")
            async with page.expect_popup() as popup_info:
                await page.click("//div[text()='工时填报单']")
            page1 = await popup_info.value
            res = await writeSchedule(page1, schedule)
            callback()
            notfoundlist += res
        # 关闭浏览器
        await context.close()
        await browser.close()
    return notfoundlist
