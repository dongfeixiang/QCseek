from github import Github, Auth


ACCESS_TOKEN = "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"


def check_version():
    '''检测release版本'''
    token = Auth.Token(ACCESS_TOKEN)
    g = Github(auth=token)


async def download():
    '''下载压缩包'''


async def unpack():
    '''解压文件包'''


async def restart():
    '''重启程序'''


if __name__ == "__main__":
    check_version()
