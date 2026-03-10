import asyncio
import json
import subprocess
import time

import websockets  # pip3 install websockets でインストール

URI = "wss://api.p2pquake.net/v2/ws"

# 起動したいアプリのフルパス
TARGET_APP_PATH = "/Users/hayashieisuke/Applications/地震ライブ.app"

# 何秒以内の連続起動を抑制するか（例: 5秒）
DEBOUNCE_SECONDS = 5

# 直近でアプリを起動した時刻（エポック秒）
last_launch_time = 0.0


def launch_app_with_debounce(reason: str) -> None:
    """短時間に何度も起動しないようにデバウンスしつつアプリを開く。"""
    global last_launch_time
    now = time.time()
    if now - last_launch_time < DEBOUNCE_SECONDS:
        print(
            f"[デバウンス] {DEBOUNCE_SECONDS}秒以内の連続起動なのでスキップ ({reason})"
        )
        return

    print(f"[起動] 地震ライブ.app を開きます ({reason})")
    last_launch_time = now
    subprocess.run(["open", TARGET_APP_PATH])


async def monitor():
    while True:
        try:
            async with websockets.connect(URI) as ws:
                print("P2P地震情報 WebSocket に接続しました")

                async for msg in ws:
                    data = json.loads(msg)

                    code = data.get("code")
                    print(f"受信コード: {code}")
                    if code != 555:
                        print(json.dumps(data, ensure_ascii=False, indent=2))

                    # 1. EEW発表検出（554） → 即起動候補
                    if code == 554:
                        print("EEW発表検出(554)受信:", data)
                        launch_app_with_debounce("EEW発表検出(554)")

                    # 2. EEW（緊急地震速報 警報） → 即起動候補
                    elif code == 556:
                        print("EEW受信(556):", data)
                        launch_app_with_debounce("EEW(556)")
                    # 3. 津波予報（552） → 即起動候補
                    elif code == 552:
                        print("津波予報(552)受信:", data)
                        launch_app_with_debounce("津波予報(552)")
                    # 4. 通常の地震情報 → 震度1以上なら起動候補
                    elif code == 551:
                        eq = data.get("earthquake", {})
                        max_scale = eq.get("maxScale")

                        # maxScale: 0,10,20,30,40,45,50,55,60,70
                        # = 震度0,1,2,3,4,5弱,5強,6弱,6強,7
                        if max_scale is not None and max_scale >= 10:  # 震度1以上
                            print("地震情報（震度1以上）受信(551):", data)
                            launch_app_with_debounce("地震情報(551, 震度1以上)")

                    # 552(津波予報)は今回はトリガーにしないので elif は書かない

        except Exception as e:
            print("エラー:", e)
            print("5秒後に再接続します")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(monitor())
