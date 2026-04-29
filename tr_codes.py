# # -*- coding: utf-8 -*-
# """
# TR Codes Reference (REST API 매핑 포함)
# """

# # 1. 계좌
# TR_CODES_ACCOUNT = {
#     "TR_ACCOUNT_NUMBER": {"api_id": "ka00001"},
#     "TR_DAILY_BALANCE_PROFIT": {"api_id": "ka01690"},
#     "TR_REALIZED_PROFIT_DATE": {"api_id": "ka10072"},
#     "TR_REALIZED_PROFIT_PERIOD": {"api_id": "ka10073"},
#     "TR_REALIZED_PROFIT": {"api_id": "ka10074"},
#     "TR_UNFILLED_ORDER": {"api_id": "ka10075"},
#     "TR_FILLED_ORDER": {"api_id": "ka10076"},
#     "TR_TODAY_REALIZED_DETAIL": {"api_id": "ka10077"},
#     "TR_ACCOUNT_PROFIT": {"api_id": "ka10085"},
#     "TR_UNFILLED_SPLIT_DETAIL": {"api_id": "ka10088"},
#     "TR_TODAY_TRADE_LOG": {"api_id": "ka10170"},
#     "TR_DEPOSIT_DETAIL": {"api_id": "kt00001"},
#     "TR_DAILY_EST_ASSET": {"api_id": "kt00002"},
#     "TR_EST_ASSET": {"api_id": "kt00003"},
#     "TR_ACCOUNT_EVAL": {"api_id": "kt00004"},
#     "TR_FILLED_BALANCE": {"api_id": "kt00005"},
#     "TR_ACCOUNT_ORDER_DETAIL": {"api_id": "kt00007"},
#     "TR_ACCOUNT_SETTLEMENT": {"api_id": "kt00008"},
#     "TR_ACCOUNT_ORDER_STATUS": {"api_id": "kt00009"},
#     "TR_WITHDRAW_AVAILABLE": {"api_id": "kt00010"},
#     "TR_MARGIN_ORDER_QTY": {"api_id": "kt00011"},
#     "TR_CREDIT_MARGIN_ORDER_QTY": {"api_id": "kt00012"},
#     "TR_MARGIN_DETAIL": {"api_id": "kt00013"},
#     "TR_TRADING_HISTORY": {"api_id": "kt00015"},
#     "TR_DAILY_ACCOUNT_PROFIT_DETAIL": {"api_id": "kt00016"},
#     "TR_TODAY_ACCOUNT_STATUS": {"api_id": "kt00017"},
#     "TR_ACCOUNT_BALANCE_DETAIL": {"api_id": "kt00018"},
#     "TR_GOLD_BALANCE": {"api_id": "kt50020"},
#     "TR_GOLD_DEPOSIT": {"api_id": "kt50021"},
#     "TR_GOLD_ORDER_ALL": {"api_id": "kt50030"},
#     "TR_GOLD_ORDER": {"api_id": "kt50031"},
#     "TR_GOLD_TRADING_HISTORY": {"api_id": "kt50032"},
#     "TR_GOLD_UNFILLED": {"api_id": "kt50075"},
# }
# ACCOUNT_URI = "/uapi/domestic-stock/v1/trading/inquire-account"
# ACCOUNT_TR_ID = "TTTC0001R"

# # 2. 공매도
# TR_CODES_SHORT_SELL = {
#     "TR_SHORT_SELL_TREND": {"api_id": "ka10014"},
# }
# SHORTSELL_URI = "/uapi/domestic-stock/v1/quotations/inquire-shortsell"
# SHORTSELL_TR_ID = "FHKST03020100"

# # 3. 기관/외국인
# TR_CODES_INSTITUTION_FOREIGN = {
#     "TR_FOREIGN_TRADE_TREND": {"api_id": "ka10008"},
#     "TR_INSTITUTION_TRADE": {"api_id": "ka10009"},
#     "TR_INST_FOREIGN_CONTINUOUS": {"api_id": "ka10131"},
# }
# INSTITUTION_URI = "/uapi/domestic-stock/v1/quotations/inquire-investor"
# INSTITUTION_TR_ID = "FHKST03020200"

# # 4. 대차거래
# TR_CODES_SECURITIES_LENDING = {
#     "TR_SECURITIES_LENDING_TREND": {"api_id": "ka10068"},
#     "TR_SECURITIES_LENDING_TOP10": {"api_id": "ka10069"},
#     "TR_SECURITIES_LENDING_TREND_BY_STOCK": {"api_id": "ka20068"},
#     "TR_SECURITIES_LENDING_HISTORY": {"api_id": "ka90012"},
# }
# LENDING_URI = "/uapi/domestic-stock/v1/quotations/inquire-lending"
# LENDING_TR_ID = "FHKST03020300"

# # 5. 순위정보
# TR_CODES_RANKING = {
#     "TR_TOP_BID_QTY": {"api_id": "kai0020"},
#     "TR_TOP_BID_SURGE": {"api_id": "kai0021"},
#     "TR_TOP_BID_UL_SURGE": {"api_id": "kai0022"},
#     "TR_VOLUME_SURGE": {"api_id": "kai0023"},
#     "TR_TOP_CHANGE_RATE": {"api_id": "kai0027"},
#     "TR_TOP_EXPECT_CHANGE": {"api_id": "kai0029"},
#     "TR_TOP_TODAY_VOLUME": {"api_id": "kai0030"},
#     "TR_TOP_YESTERDAY_VOLUME": {"api_id": "kai0031"},
#     "TR_TOP_TRADE_VALUE": {"api_id": "kai0032"},
#     "TR_TOP_CREDIT_RATIO": {"api_id": "kai0033"},
#     "TR_TOP_FOREIGN_PERIOD": {"api_id": "kai0034"},
#     "TR_TOP_FOREIGN_CONTINUOUS": {"api_id": "kai0035"},
#     "TR_TOP_FOREIGN_LIMIT": {"api_id": "kai0036"},
#     "TR_TOP_FOREIGN_BRANCH": {"api_id": "kai0037"},
#     "TR_TOP_BROKER_STOCK": {"api_id": "kai0038"},
#     "TR_TOP_BROKER": {"api_id": "kai0039"},
#     "TR_TOP_TODAY_TRADER": {"api_id": "kai0040"},
#     "TR_TOP_NET_BUY_TRADER": {"api_id": "kai0042"},
#     "TR_TOP_TODAY_EXIT_TRADER": {"api_id": "kai0053"},
#     "TR_TOP_SAME_HAND": {"api_id": "kai0062"},
#     "TR_TOP_INTRADAY_INVESTOR": {"api_id": "kai0065"},
#     "TR_TOP_AFTER_HOURS_CHANGE": {"api_id": "kai0098"},
#     "TR_TOP_FOREIGN_INST": {"api_id": "kai90009"},
# }
# RANKING_URI = "/uapi/domestic-stock/v1/quotations/inquire-ranking"
# RANKING_TR_ID = "FHKST03020400"

# # 6. 시세
# TR_CODES_MARKET = {
#     "TR_STOCK_QUOTE": {"api_id": "ka10004"},
#     "TR_STOCK_DAY_WEEK_MONTH": {"api_id": "ka10005"},
#     "TR_STOCK_MARKET": {"api_id": "ka10006"},
#     "TR_PRICE_TABLE_INFO": {"api_id": "ka10007"},
#     "TR_RIGHTS_ISSUE_QUOTE": {"api_id": "ka10011"},
#     "TR_DAILY_INST_TRADE": {"api_id": "ka10044"},
#     "TR_INST_TRADE_TREND": {"api_id": "ka10045"},
#     "TR_TRADE_STRENGTH_BY_TIME": {"api_id": "ka10046"},
#     "TR_TRADE_STRENGTH_BY_DAY": {"api_id": "ka10047"},
#     "TR_INTRADAY_INVESTOR_TRADE": {"api_id": "ka10063"},
#     "TR_AFTER_MARKET_INVESTOR_TRADE": {"api_id": "ka10066"},
#     "TR_BROKER_STOCK_TREND": {"api_id": "ka10078"},
#     "TR_DAILY_STOCK_PRICE": {"api_id": "ka10086"},
#     "TR_AFTER_HOURS_SINGLE_PRICE": {"api_id": "ka10087"},
#     "TR_GOLD_TRADE_TREND": {"api_id": "ka50010"},
#     "TR_GOLD_DAILY_TREND": {"api_id": "ka50012"},
#     "TR_GOLD_EXPECTED_TRADE": {"api_id": "ka50087"},
#     "TR_GOLD_PRICE_INFO": {"api_id": "ka50100"},
#     "TR_GOLD_BID_INFO": {"api_id": "ka50101"},
#     "TR_PROGRAM_TRADE_BY_TIME": {"api_id": "ka90005"},
#     "TR_PROGRAM_ARBITRAGE_BALANCE": {"api_id": "ka90006"},
#     "TR_PROGRAM_TRADE_ACCUMULATED": {"api_id": "ka90007"},
#     "TR_PROGRAM_TRADE_BY_STOCK_TIME": {"api_id": "ka90008"},
#     "TR_PROGRAM_TRADE_BY_DATE": {"api_id": "ka90010"},
#     "TR_PROGRAM_TRADE_BY_STOCK_DATE": {"api_id": "ka90013"},
# }
# MARKET_URI = "/uapi/domestic-stock/v1/quotations/inquire-price"
# MARKET_TR_ID = "FHKST01010100"

# # 7. 신용주문
# TR_CODES_CREDIT_ORDER = {
#     "TR_CREDIT_BUY": {"api_id": "kt10006"},
#     "TR_CREDIT_SELL": {"api_id": "kt10007"},
#     "TR_CREDIT_MODIFY": {"api_id": "kt10008"},
#     "TR_CREDIT_CANCEL": {"api_id": "kt10009"},
# }
# CREDIT_URI = "/uapi/domestic-stock/v1/trading/order-credit"
# CREDIT_TR_ID = "TTTC0801U"

# # 8. 실시간시세
# TR_CODES_REALTIME = {
#     "TR_REALTIME_RANK": {"api_id": "ka00198"},
# }
# REALTIME_URI = "/uapi/domestic-stock/v1/quotations/inquire-realtime"
# REALTIME_TR_ID = "FHKST03020500"

# # 9. 업종
# TR_CODES_INDUSTRY = {
#     "TR_INDUSTRY_PROGRAM": {"api_id": "ka10010"},
#     "TR_INDUSTRY_INVESTOR_NETBUY": {"api_id": "ka10051"},
#     "TR_INDUSTRY_CURRENT_PRICE": {"api_id": "ka20001"},
#     "TR_INDUSTRY_DAILY_PRICE": {"api_id": "ka20002"},
#     "TR_ALL_INDUSTRY_INDEX": {"api_id": "ka20003"},
#     "TR_INDUSTRY_CURRENT_PRICE_BY_GROUP": {"api_id": "ka20009"},
# }
# INDUSTRY_URI = "/uapi/domestic-stock/v1/quotations/inquire-industry"
# INDUSTRY_TR_ID = "FHKST03020600"

# # 10. 조건검색
# TR_CODES_CONDITIONAL_SEARCH = {
#     "TR_CONDITION_LIST": {"api_id": "ka10171"},
#     "TR_CONDITION_REQUEST": {"api_id": "ka10172"},
#     "TR_CONDITION_REQUEST_REALTIME": {"api_id": "ka10173"},
#     "TR_CONDITION_CANCEL_REALTIME": {"api_id": "ka10174"},
# }
# CONDITION_URI = "/uapi/domestic-stock/v1/quotations/inquire-condition"
# CONDITION_TR_ID = "FHKST03060100"

# # 11. 종목정보
# TR_CODES_STOCK_INFO = {
#     "TR_STOCK_BASIC_INFO": {"api_id": "ka10001"},
#     "TR_STOCK_TRADER": {"api_id": "ka10002"},
#     "TR_TRADE_INFO": {"api_id": "ka10003"},
#     "TR_CREDIT_TRADE": {"api_id": "ka10013"},
#     "TR_DAILY_TRADE_DETAIL": {"api_id": "ka10015"},
#     "TR_HIGH_LOW_PRICE": {"api_id": "ka10016"},
#     "TR_LIMIT_PRICE": {"api_id": "ka10017"},
#     "TR_NEAR_HIGH_LOW": {"api_id": "ka10018"},
#     "TR_PRICE_VOLATILITY": {"api_id": "ka10019"},
#     "TR_VOLUME_UPDATE": {"api_id": "ka10024"},
#     "TR_SUPPLY_DEMAND_CONCENTRATION": {"api_id": "ka10025"},
#     "TR_PER_HIGH_LOW": {"api_id": "ka10026"},
#     "TR_OPEN_CHANGE_RATE": {"api_id": "ka10028"},
#     "TR_TRADER_SUPPLY_DEMAND_ANALYSIS": {"api_id": "ka10043"},
#     "TR_TRADER_MOMENT_VOLUME": {"api_id": "ka10052"},
#     "TR_VOLATILITY_CONTROL_STOCK": {"api_id": "ka10054"},
#     "TR_TODAY_YESTERDAY_TRADE": {"api_id": "ka10055"},
#     "TR_DAILY_INVESTOR_TRADE": {"api_id": "ka10058"},
#     "TR_STOCK_INVESTOR_INST": {"api_id": "ka10059"},
#     "TR_STOCK_INVESTOR_INST_SUM": {"api_id": "ka10061"},
#     "TR_TODAY_YESTERDAY_TRADE_ALT": {"api_id": "ka10084"},
#     "TR_INTEREST_STOCK_INFO": {"api_id": "ka10095"},
#     "TR_STOCK_INFO_LIST": {"api_id": "ka10100"},
# }
# STOCKINFO_URI = "/uapi/domestic-stock/v1/quotations/inquire-stockinfo"
# STOCKINFO_TR_ID = "FHKST03020700"

# # 12. 주문
# TR_CODES_ORDER = {
#     "TR_ORDER_CASH_BUY": {"api_id": "kt20001"},
#     "TR_ORDER_CASH_SELL": {"api_id": "kt20002"},
#     "TR_ORDER_CASH_MODIFY": {"api_id": "kt20003"},
#     "TR_ORDER_CASH_CANCEL": {"api_id": "kt20004"},
# }
# ORDER_URI = "/uapi/domestic-stock/v1/trading/order-cash"
# ORDER_TR_ID = "TTTC0802U"

# # 13. 차트
# TR_CODES_CHART = {
#     "TR_STOCK_DAY_WEEK_MONTH": {"api_id": "ka10005"},
# }
# CHART_URI = "/uapi/domestic-stock/v1/quotations/inquire-chart"
# CHART_TR_ID = "FHKST03020800"

# # 14. 테마
# TR_CODES_THEME = {
#     "TR_THEME_LIST": {"api_id": "ka40001"},
#     "TR_THEME_DETAIL": {"api_id": "ka40002"},
# }
# THEME_URI = "/uapi/domestic-stock/v1/quotations/inquire-theme"
# THEME_TR_ID = "FHKST03020900"

# # 15. ELW
# TR_CODES_ELW = {
#     "TR_ELW_BASIC_INFO": {"api_id": "ka30010"},
#     "TR_ELW_DAILY_PRICE": {"api_id": "ka30011"},
#     "TR_ELW_TRADE_DETAIL": {"api_id": "ka30012"},
#     "TR_ELW_ISSUE_INFO": {"api_id": "ka30013"},
# }
# ELW_URI = "/uapi/domestic-stock/v1/quotations/inquire-elw"
# ELW_TR_ID = "FHKST03040100"

# # 16. ETF
# TR_CODES_ETF = {
#     "TR_ETF_BASIC_INFO": {"api_id": "ka20010"},
#     "TR_ETF_DAILY_PRICE": {"api_id": "ka20011"},
#     "TR_ETF_TRADE_DETAIL": {"api_id": "ka20012"},
#     "TR_ETF_HOLDINGS": {"api_id": "ka20013"},
#     "TR_ETF_NAV": {"api_id": "ka20014"},
# }
# ETF_URI = "/uapi/domestic-stock/v1/quotations/inquire-etf"
# ETF_TR_ID = "FHKST03030100"
# 차트 관련
TR_CODES_CHART = {
    "TR_STOCK_DAILY_CHART": {"api_id": "ka10081"},
    "TR_STOCK_WEEKLY_CHART": {"api_id": "ka10082"},
    "TR_STOCK_MONTHLY_CHART": {"api_id": "ka10083"},
    "TR_STOCK_YEARLY_CHART": {"api_id": "ka10094"},
}
CHART_URI = "/api/dostk/chart"
CHART_TR_ID = "ka10081"
CHART_API_IDS = {
    "D": "ka10081",
    "W": "ka10082",
    "M": "ka10083",
    "Y": "ka10094",
}