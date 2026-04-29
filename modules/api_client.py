import requests, json

def call_api(token, endpoint, api_id, data, cont_yn='N', next_key=''): 
    host = 'https://api.kiwoom.com'
    url = host + endpoint
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'authorization': f'Bearer {token}',
        'cont-yn': cont_yn,
        'next-key': next_key,
        'api-id': api_id,
    }
    response = requests.post(url, headers=headers, json=data)
    print('Code:', response.status_code)
    print('Header:', json.dumps({key: response.headers.get(key) for key in ['next-key','cont-yn','api-id']}, indent=4, ensure_ascii=False))
    print('Body:', json.dumps(response.json(), indent=4, ensure_ascii=False))
    return response.json()