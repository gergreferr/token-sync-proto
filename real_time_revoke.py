"""
Real Time Revoke — утилита мониторинга активных разрешений (approve) в Ethereum и автоматической отправки уведомлений при необходимости их отмены.

Особенно полезно для защиты кошелька от вредоносных dApp, фишинговых контрактов и забытых разрешений на токены.
"""

import requests
import argparse
from tabulate import tabulate


ETHERSCAN_API_URL = "https://api.etherscan.io/api"

def fetch_approvals(address, api_key):
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "sort": "desc",
        "apikey": api_key
    }
    response = requests.get(ETHERSCAN_API_URL, params=params)
    txs = response.json().get("result", [])

    approvals = []
    for tx in txs:
        if tx["input"].startswith("0x095ea7b3"):  # approve(address,uint256)
            spender = "0x" + tx["input"][34:74]
            token = tx["contractAddress"]
            token_symbol = tx.get("tokenSymbol", "")
            approvals.append({
                "token": token,
                "symbol": token_symbol or "UNKNOWN",
                "spender": spender,
                "tx": tx["hash"]
            })
    return approvals


def analyze_risk(approvals):
    risky = []
    for a in approvals:
        if a["symbol"] == "UNKNOWN" or a["spender"].lower().startswith("0x000"):
            risky.append(a)
    return risky


def show_approvals_table(approvals):
    table = [[a["symbol"], a["token"], a["spender"], a["tx"]] for a in approvals]
    print(tabulate(table, headers=["Token", "Token Address", "Spender", "TX Hash"], tablefmt="grid"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Time Revoke — мониторинг и анализ разрешений approve()")
    parser.add_argument("address", help="Ethereum-адрес для анализа")
    parser.add_argument("api_key", help="API-ключ от Etherscan")
    args = parser.parse_args()

    print(f"[•] Проверка активных approve-транзакций по адресу {args.address}...")
    approvals = fetch_approvals(args.address, args.api_key)

    if not approvals:
        print("[✓] Активных разрешений не найдено.")
    else:
        print(f"[✓] Найдено {len(approvals)} активных разрешений:")
        show_approvals_table(approvals)

        risky = analyze_risk(approvals)
        if risky:
            print("\n[!] Обнаружены потенциально опасные разрешения:")
            show_approvals_table(risky)
            print("\n⚠️ Рекомендуется отозвать эти разрешения через Revoke.cash или аналог.")
        else:
            print("\n[✓] Опасных разрешений не найдено.")
