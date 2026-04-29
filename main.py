# from modules.auth import fn_au10001
# from modules.account import fn_ka00001
# from modules.trading import fn_kt10000
# from modules.chart import fn_ka10060
# from modules.etf_elw import fn_ka40001
# from modules.quotes import WebSocketClient, SOCKET_URL

# import asyncio

# APPKEY = "106kkiYckDEfJKfG2GoYYL46FTukNEz8fseXe6f83Ao"
# SECRETKEY = "n38UhjmRSBWr6-5cm60_3XZgsCDLxsDhOpPI-y8MKo4"

# if __name__ == "__main__":
#     # 토큰 발급
#     token_info = fn_au10001({"grant_type":"client_credentials","appkey":APPKEY,"secretkey":SECRETKEY})
#     token = token_info.get("token")

#     if token:
#         # 계좌 조회
#         fn_ka00001(token, {})

#         # 매수 주문
#         fn_kt10000(token, {"dmst_stex_tp":"KRX","stk_cd":"005930","ord_qty":"1","trde_tp":"3"})

#         # 차트 조회
#         fn_ka10060(token, {"dt":"20241107","stk_cd":"005930","amt_qty_tp":"1","trde_tp":"0","unit_tp":"1000"})

#         # ETF 조회
#         fn_ka40001(token, {"stk_cd":"069500","etfobjt_idex_cd":"207","dt":"3"})

#         # 실시간 시세 WebSocket 실행
#         async def run_ws():
#             client = WebSocketClient(SOCKET_URL)
#             receive_task = asyncio.create_task(client.run())
#             await asyncio.sleep(1)
#             await client.send_message({
#                 'trnm': 'REG',
#                 'grp_no': '1',
#                 'refresh': '1',
#                 'data': [{'item': ['005930'], 'type': ['00']}]
#             })
#             await receive_task

#         asyncio.run(run_ws())

from modules.auth import fn_au10001
from modules.quotes import WebSocketClient, SOCKET_URL, root
import modules.quotes as quotes
import asyncio, threading

# 토큰 발급 및 설정
APPKEY = "106kkiYckDEfJKfG2GoYYL46FTukNEz8fseXe6f83Ao"
SECRETKEY = "n38UhjmRSBWr6-5cm60_3XZgsCDLxsDhOpPI-y8MKo4"

token_info = fn_au10001({"grant_type":"client_credentials","appkey":APPKEY,"secretkey":SECRETKEY})
token = token_info.get("token")

if token:
    quotes.ACCESS_TOKEN = token  # quotes 모듈의 ACCESS_TOKEN 설정
    quotes.ws_client = WebSocketClient(SOCKET_URL)  # WebSocket 클라이언트 생성
    print("토큰 발급 성공")
else:
    print("토큰 발급 실패")

# GUI 실행
if __name__ == "__main__":
    # WebSocket을 백그라운드에서 실행
    if quotes.ws_client:
        ws_thread = threading.Thread(target=lambda: asyncio.run(quotes.ws_client.run()), daemon=True)
        ws_thread.start()
    
    root.mainloop()

# 실제 발급받은 키 값 사용
APPKEY = "106kkiYckDEfJKfG2GoYYL46FTukNEz8fseXe6f83Ao"
SECRETKEY = "n38UhjmRSBWr6-5cm60_3XZgsCDLxsDhOpPI-y8MKo4"

def get_token():
    token_info = fn_au10001({
        "grant_type": "client_credentials",
        "appkey": APPKEY,
        "secretkey": SECRETKEY
    })
    print("토큰 응답:", token_info)
    return token_info.get("access_token") or token_info.get("token")

async def refresh_token(client):
    while True:
        await asyncio.sleep(3300)  # 55분마다 갱신
        quotes.ACCESS_TOKEN = get_token()
        print("토큰 갱신 완료:", quotes.ACCESS_TOKEN)
        await client.disconnect()
        await client.connect()

async def run_ws():
    global ws_client_ref
    client = WebSocketClient(SOCKET_URL)
    ws_client_ref = client
    quotes.ws_client = client
    
    asyncio.create_task(refresh_token(client))
    
    # 로그인 후 기본 종목 구독
    await client.connect()
    await asyncio.sleep(1)
    await client.subscribe("005930")  # 삼성전자 구독
    
    await client.receive_messages()

ws_client_ref = None

def on_subscribe_clicked():
    """GUI 버튼 클릭 시 종목 구독"""
    code = quotes.entry_code.get().strip()
    if not code:
        quotes.label_status.config(text="종목코드를 입력하세요", fg="red")
        return
    
    if ws_client_ref:
        # 기존 구독 해제 후 새로운 종목 구독
        if quotes.current_code:
            asyncio.run_coroutine_threadsafe(
                ws_client_ref.unsubscribe(quotes.current_code),
                loop
            )
        asyncio.run_coroutine_threadsafe(
            ws_client_ref.subscribe(code),
            loop
        )

loop = None

def start_asyncio_loop():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_ws())

if __name__ == "__main__":
    # 최초 토큰 발급
    quotes.ACCESS_TOKEN = get_token()
    print("최초 토큰 발급:", quotes.ACCESS_TOKEN)

    # 버튼 클릭 이벤트 연결
    quotes.btn_subscribe.config(command=on_subscribe_clicked)

    # WebSocket 루프를 별도 스레드에서 실행
    threading.Thread(target=start_asyncio_loop, daemon=True).start()

    # Tkinter GUI는 메인 스레드에서 실행
    quotes.root.mainloop()