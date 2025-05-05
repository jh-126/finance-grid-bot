import subprocess
import time

while True:
    print("啟動交易機器人...")
    try:
        subprocess.run(["python3", "main.py"])
    except Exception as e:
        print(f"主程式崩潰，錯誤：{e}")
    print("主程式退出，3 秒後重啟")
    time.sleep(3)
