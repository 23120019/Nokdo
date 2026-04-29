from modules.api_client import call_api
import asyncio, websockets, json
import logging
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from modules.chart import fn_ka10060  # 차트 데이터 가져오기
import datetime

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def fn_ka10004(token, params):  # 주식 호가 요청
    return call_api(token, '/api/dostk/mrkcond', 'ka10004', params)

SOCKET_URL = 'wss://api.kiwoom.com:10000/api/dostk/websocket'
ACCESS_TOKEN = None  # main.py에서 갱신해줌

# 로그 설정
logging.basicConfig(filename="quotes.log", level=logging.INFO, format="%(asctime)s %(message)s")

# Tkinter GUI 초기화
root = tk.Tk()
root.title("실시간 시세 차트")

# 종목 선택 프레임
frame_top = tk.Frame(root)
frame_top.pack()
tk.Label(frame_top, text="종목코드:").pack(side=tk.LEFT)
entry_code = tk.Entry(frame_top, width=10)
entry_code.pack(side=tk.LEFT, padx=5)
entry_code.insert(0, "005930")  # 삼성전자 기본값

# 구독 버튼과 상태 표시
btn_subscribe = tk.Button(frame_top, text="차트 조회")
btn_subscribe.pack(side=tk.LEFT, padx=5)
label_status = tk.Label(frame_top, text="대기중", fg="gray")
label_status.pack(side=tk.LEFT, padx=10)

# 차트 조회 버튼 이벤트
def on_load_chart():
    global prices, dates
    code = entry_code.get().strip()
    if not code:
        label_status.config(text="종목코드 입력 필요", fg="red")
        return
    
    if not ACCESS_TOKEN:
        label_status.config(text="토큰 없음", fg="red")
        return
    
    label_status.config(text="데이터 조회중...", fg="blue")
    
    # 차트 데이터 조회
    today = datetime.date.today().strftime("%Y%m%d")
    params = {
        "dt": today,  # 오늘 날짜로 설정
        "stk_cd": code,
        "amt_qty_tp": "1",
        "trde_tp": "0",
        "unit_tp": "1000"
    }
    
    try:
        response = fn_ka10060(ACCESS_TOKEN, params)
        print(f"Chart response: {response}")  # 디버깅
        print(f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")  # 응답 구조 확인
        
        # 데이터 파싱 (실제 응답 구조에 맞춤)
        temp_prices = []
        temp_dates = []
        if isinstance(response, dict):
            # 가능한 데이터 키들 시도
            data = response.get('stk_invsr_orgn_chart') or response.get('data') or response.get('output')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # cur_prc 키 사용
                        val = item.get('cur_prc')
                        date = item.get('dt')
                        if val and date:
                            try:
                                # + 또는 - 제거 후 float 변환
                                clean_val = val.replace('+', '').replace('-', '')
                                price = float(clean_val)
                                temp_prices.append(price)
                                if isinstance(date, str) and len(date) == 8:
                                    temp_dates.append(f"{date[4:6]}/{date[6:8]}")
                                else:
                                    temp_dates.append(str(date))
                            except ValueError:
                                pass
            else:
                print(f"Data is not a list: {type(data)}, value: {data}")
            
            # 데이터를 과거에서 최신으로 정렬 (역순)
            temp_prices.reverse()
            temp_dates.reverse()
        
        print(f"Parsed prices count: {len(temp_prices)}, dates count: {len(temp_dates)}")  # 디버깅
        
        if temp_prices:
            prices.clear()
            dates.clear()
            prices.extend(temp_prices)
            dates.extend(temp_dates)
            
            # 한 번에 모든 데이터 설정
            line.set_data(range(len(prices)), prices)
            if dates:
                ax.set_xticks(range(len(dates)))
                ax.set_xticklabels(dates, rotation=45, fontsize=8)
            ax.relim()
            ax.autoscale_view()
            canvas.draw()
            
            label_status.config(text=f"데이터 로드 완료 ({len(prices)}개)", fg="green")
        else:
            label_status.config(text="가격 데이터 없음", fg="orange")
            print("No prices found in response")
    except Exception as e:
        print(f"Error: {e}")
        label_status.config(text=f"오류: {str(e)}", fg="red")

btn_subscribe.config(command=on_load_chart)

# 차트 초기화 객체
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r-')
ax.set_xlabel('일자')
ax.set_ylabel('가격(원)')
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

prices = []
dates = []

def update_chart(new_price):
    global prices, dates
    prices.append(new_price)
    line.set_data(range(len(prices)), prices)
    if dates:
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels(dates, rotation=45, fontsize=8)
    ax.relim()
    ax.autoscale_view()
    canvas.draw()

def clear_chart():
    """차트 초기화"""
    global prices, dates
    prices = []
    dates = []
    line.set_data([], [])
    ax.set_xticks([])
    ax.set_xticklabels([])
    ax.relim()
    ax.autoscale_view()
    canvas.draw()

def update_chart_safe(new_price):
    root.after(0, lambda: update_chart(new_price))

class WebSocketClient:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.connected = False
        self.keep_running = True
        self.subscribed_codes = []  # 구독 중인 종목 codes

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            logging.info("서버와 연결되었습니다.")
            param = {'trnm': 'LOGIN', 'token': ACCESS_TOKEN}
            await self.send_message(param)
        except Exception as e:
            logging.error(f'Connection error: {e}')
            self.connected = False

    async def subscribe(self, code):
        """종목 실시간 시세 구독"""
        global current_code
        if not self.connected:
            await self.connect()
        
        current_code = code
        self.subscribed_codes = [code]
        clear_chart()  # 새 종목 구독 시 차트 초기화
        
        param = {
            'trnm': 'REG',
            'grp_no': '1',
            'refresh': '1',
            'data': [{'item': [code], 'type': ['00']}]
        }
        await self.send_message(param)
        label_status.config(text=f"구독중: {code}", fg="green")
        logging.info(f"종목 {code} 구독 시작")

    async def unsubscribe(self, code):
        """종목 구독 해제"""
        if not self.connected:
            return
        
        param = {
            'trnm': 'UNREG',
            'grp_no': '1',
            'data': [{'item': [code], 'type': ['00']}]
        }
        await self.send_message(param)
        self.subscribed_codes.remove(code)
        logging.info(f"종목 {code} 구독 해제")

    async def send_message(self, message):
        if not self.connected:
            await self.connect()
        if self.connected:
            if not isinstance(message, str):
                message = json.dumps(message)
            await self.websocket.send(message)
            logging.info(f'Message sent: {message}')

    async def receive_messages(self):
        while self.keep_running:
            try:
                response = json.loads(await self.websocket.recv())
                print(f"Received: {response}")  # 디버깅용 출력
                if response.get('trnm') == 'LOGIN':
                    if response.get('return_code') != 0:
                        logging.error(f'로그인 실패: {response.get("return_msg")}')
                        await self.disconnect()
                    else:
                        logging.info('로그인 성공')
                elif response.get('trnm') == 'PING':
                    await self.send_message(response)
                else:
                    logging.info(f'실시간 응답: {response}')

                    # 여러 필드에서 가격 추출
                    price = None
                    for key in ["cur_prc", "price", "etfprft_rt"]:
                        if key in response:
                            try:
                                val = response[key]
                                if isinstance(val, str):
                                    val = val.replace("+","").replace("-","")
                                price = float(val)
                                print(f"Extracted price: {price} from {key}")  # 디버깅용
                                break
                            except Exception as e:
                                logging.error(f"{key} 변환 실패: {response.get(key)} / {e}")

                    if price is not None:
                        update_chart_safe(price)

            except websockets.ConnectionClosed:
                logging.warning('Connection closed')
                self.connected = False
                await self.websocket.close()

    async def run(self):
        await self.connect()
        await self.receive_messages()

    async def disconnect(self):
        self.keep_running = False
        if self.connected and self.websocket:
            await self.websocket.close()
            self.connected = False
            logging.info('Disconnected')