import asyncio
import json
import subprocess

import websockets  # pip3 install websockets でインストール

URI = "wss://api.p2pquake.net/v2/ws"

# 起動したいアプリのフルパス
TARGET_APP_PATH = "/Users/hayashieisuke/Applications/地震ライブ.app"


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
                    # 1. EEW（緊急地震速報） → 来たら即起動
                    if code == 556:
                        print("EEW受信:", data)
                        subprocess.run(["open", TARGET_APP_PATH])

                    # 2. 通常の地震情報 → 震度1以上なら起動
                    elif code == 551:
                        eq = data.get("earthquake", {})
                        max_scale = eq.get("maxScale")

                        # maxScale: 0,10,20,30,40,45,50,55,60,70 = 震度0,1,2,3,4,5弱,5強,6弱,6強,7
                        if max_scale is not None and max_scale >= 10:  # 震度1以上
                            print("地震情報（震度1以上）受信:", data)
                            subprocess.run(["open", TARGET_APP_PATH])

        except Exception as e:
            print("エラー:", e)
            print("5秒後に再接続します")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(monitor())
