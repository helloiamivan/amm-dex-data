import json, requests
from web3 import Web3
from flask import Flask, request

app = Flask(__name__)

INFURA_URL = 'https://mainnet.infura.io/v3/a51f116d93704289b88297a22f716720'

def getABI( smartContractName ):
 
    with open(f'abi/{smartContractName}.json') as f:
        data = json.load(f)
 
    return data

def getPoolInfo( smartContractName, pairAddress, lpTokens ):

    web3 = Web3(Web3.HTTPProvider(INFURA_URL))

    SUSHISWAP_ABI = getABI( smartContractName )
    TOKEN_ABI     = getABI( 'token' )

    pairContract = web3.eth.contract( address = pairAddress, abi = SUSHISWAP_ABI )

    token0_reserve, token1_reserve, lastblock = pairContract.functions.getReserves().call()
    
    totalSupplyLP = pairContract.functions.totalSupply().call()

    token0_address = pairContract.functions.token0().call()
    
    token1_address = pairContract.functions.token1().call()

    poolInfo = {
        'Owned LP Tokens'          : lpTokens,
        'Total LP Tokens'          : totalSupplyLP / 1E18,
        'Owned LP Tokens Percent'  : lpTokens * 100.0 / ( totalSupplyLP / 1E18 ),
        'Owned Token 0'            : (lpTokens / totalSupplyLP) * token0_reserve,
        'Owned Token 1'            : (lpTokens / totalSupplyLP) * token1_reserve,
        'Total Token 0 Reserve'    : token0_reserve / 1E18,
        'Total Token 1 Reserve'    : token1_reserve / 1E18,
        'Last Block Time'          : lastblock,
        'Pair Address'             : pairAddress
    }

    tokenContract = web3.eth.contract( address = pairAddress, abi = TOKEN_ABI )

    tokenContract.functions.symbol().call()

    for i,tokenAddress, in enumerate([token0_address, token1_address]):
        tokenContract = web3.eth.contract( address = tokenAddress, abi = TOKEN_ABI )
        poolInfo.update({ f'Token {i} Symbol' : tokenContract.functions.symbol().call() } )

    return poolInfo

# Flask app starts
@app.route('/sushiswap/poolinfo', methods = ['GET'])
def sushiswap_poolinfo():
    pairAddress       = request.args.get('pa')
    lpTokens          = float(request.args.get('lp'))

    '''0xb5De0C3753b6E1B4dBA616Db82767F17513E6d4E'''

    poolInfo = getPoolInfo( smartContractName = 'sushiswap_pair' ,
                            pairAddress = pairAddress , 
                            lpTokens = lpTokens )

    return poolInfo

if __name__ == '__main__':
    app.run(threaded = True)
