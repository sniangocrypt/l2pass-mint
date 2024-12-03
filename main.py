import asyncio
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.exceptions import TransactionNotFound
import json
import aiofiles


class Wallet:
    def __init__(self, private_key, rpc_url, contract_address, abi_path):
        self.private_key = private_key
        self.rpc_url = rpc_url
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        self.address = self.w3.eth.account.from_key(self.private_key).address
        self.contract_address = self.w3.to_checksum_address(contract_address)
        self.contract = None
        self.abi_path = abi_path

    async def load_contract(self):
        async with aiofiles.open(self.abi_path, 'r') as abi_file:
            abi = json.loads(await abi_file.read())
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)

    async def fetch_balances(self, address):
        balance_eth = await self.w3.eth.get_balance(address)
        return f"eth: {self.w3.from_wei(balance_eth, 'ether')}"

    async def need_balance(self, address, value):
        balance_eth = await self.w3.eth.get_balance(address)
        balance = self.w3.from_wei(balance_eth, 'ether')
        if float(balance) - value*0.000337 <= 0:
            print("Не хватает эфира для минта")
            exit()


    async def mint_nft(self, value):
        tx = await self.contract.functions.mint(value
        ).build_transaction({
            "chainId": int(await self.w3.eth.chain_id),
            "from": f"{self.address}",
            "value": "0x12f2a36ecd555",
            "maxFeePerGas": int(await self.w3.eth.gas_price * 1.25 + await self.w3.eth.max_priority_fee),
            "maxPriorityFeePerGas": await self.w3.eth.max_priority_fee,
            "nonce": await self.w3.eth.get_transaction_count(self.address)
        })
        tx['gas'] = int((await self.w3.eth.estimate_gas(tx)) * 1.5)
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        return await self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)


async def main():
    print("Введите приватный ключ")
    private_key = f"{input()}"
    print("В какой сети будет минт? Ответ укажчите числом варианта[1-ARB / 2-OP/]")
    while True:
        rpc_url = input()
        if rpc_url == "1":
            rpc_url = 'https://arb-pokt.nodies.app'
            exp = "https://arbiscan.io/tx/"
            break
        elif rpc_url == "2":
            rpc_url = 'https://endpoints.omniatech.io/v1/op/mainnet/public'
            exp = "https://optimistic.etherscan.io/tx/"
            break
        else:print("Выбранная сеть не поддерживается, укажите ARB или OP")
    contract_address = "0x0000049F63Ef0D60aBE49fdD8BEbfa5a68822222"
    abi_path = "abi.json"
    print("Укажите количество нфт для минта")
    value = int(input())  # токены в единицах минимального значения (mwei)


    wallet = Wallet(private_key, rpc_url, contract_address, abi_path)

    await wallet.load_contract()

    await wallet.need_balance(wallet.address, value)

    sender_balances = await wallet.fetch_balances(wallet.address)
    print(f"Баланс отправителя: {sender_balances}")


    try:
        tx_hash = await wallet.mint_nft(value)
        print(f"Транзакция отправлена: {exp}{tx_hash.hex()}")
    except Exception as e:
        print(f"Ошибка при отправке транзакции: {e}")

    #Проверка балансов после перевода
    sender_balances = await wallet.fetch_balances(wallet.address)
    print(f"Баланс отправителя после: {sender_balances}")


asyncio.run(main())
