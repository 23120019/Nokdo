from modules.api_wrapper import request_tr

token = "발급받은토큰"  # 실제 발급받은 토큰을 넣으세요

# 필요한 순간에만 호출
result = request_tr(token, "TR_00001", {"param1": "value"})
print("계좌번호조회 결과:", result)

result2 = request_tr(token, "TR_10076", {"param2": "value"})
print("체결요청 결과:", result2)