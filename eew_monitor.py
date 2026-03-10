import asyncio
import json
import subprocess
import time

import websockets  # pip3 install websockets でインストール

URI = "wss://api.p2pquake.net/v2/ws"

# 開きたい YouTube ライブのURL
YOUTUBE_URL = "https://www.youtube.com/live/c7_kqMFDE8c?si=KJ2P7ej55xRp1GK0"

# 何秒以内の連続起動を抑制するか（例: 5秒）
DEBOUNCE_SECONDS = 5
last_launch_time = 0.0


def launch_app_with_debounce(reason: str) -> None:
    """短時間に何度も起動しないようにデバウンスしつつ Brave で動画を開く。"""
    global last_launch_time
    now = time.time()
    if now - last_launch_time < DEBOUNCE_SECONDS:
        print(
            f"[デバウンス] {DEBOUNCE_SECONDS}秒以内の連続起動なのでスキップ ({reason})"
        )
        return

    print(f"[起動] Brave で 地震ライブ を開きます ({reason})")
    last_launch_time = now
    subprocess.run(["open", "-a", "Brave Browser", YOUTUBE_URL])


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

                    # 1. EEW発表検出（554）
                    if code == 554:
                        print("EEW発表検出(554)受信:", data)
                        launch_app_with_debounce("EEW発表検出(554)")

                    # 2. EEW（緊急地震速報 警報）
                    elif code == 556:
                        print("EEW受信(556):", data)
                        launch_app_with_debounce("EEW(556)")

                    # 3. 津波予報（552）
                    elif code == 552:
                        print("津波予報(552)受信:", data)
                        launch_app_with_debounce("津波予報(552)")

                    # 4. 地震情報（551）→ 震度1以上
                    elif code == 551:
                        eq = data.get("earthquake", {})
                        max_scale = eq.get("maxScale")
                        if max_scale is not None and max_scale >= 10:
                            print("地震情報（震度1以上）受信(551):", data)
                            launch_app_with_debounce("地震情報(551, 震度1以上)")

        except Exception as e:
            print("エラー:", e)
            print("5秒後に再接続します")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(monitor())
