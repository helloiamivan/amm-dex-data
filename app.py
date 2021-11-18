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
    # TODO: Clean up code to make class
    # TODO: Structure output JSON as a nested structure
    # TODO: Query ABI as API and cache ABI and statics such as decimals and symbols locally

    web3 = Web3(Web3.HTTPProvider(INFURA_URL))

    SUSHISWAP_ABI = getABI( smartContractName )

    TOKEN_ABI     = getABI( 'token' )

    pairContract = web3.eth.contract( address = pairAddress, abi = SUSHISWAP_ABI )

    token0_reserve, token1_reserve, lastblock = pairContract.functions.getReserves().call()
    
    totalSupplyLP  = pairContract.functions.totalSupply().call()
    lpDecimal      = 10 ** pairContract.functions.decimals().call()
    token0_address = pairContract.functions.token0().call()
    token1_address = pairContract.functions.token1().call()

    # Pool information dictionary to be returned in API
    poolInfo = {}

    for i,tokenAddress, in enumerate([token0_address, token1_address]):
        tokenContract = web3.eth.contract( address = tokenAddress, abi = TOKEN_ABI )
        poolInfo.update({ f'Token {i} Symbol'  : tokenContract.functions.symbol().call() } )
        poolInfo.update({ f'Token {i} Decimal' : tokenContract.functions.decimals().call()})
    
    # Get the divisors for each token
    token0Decimal = 10 ** poolInfo['Token 0 Decimal']
    token1Decimal = 10 ** poolInfo['Token 1 Decimal']
    
    poolInfo.update({
        'Owned LP Tokens'          : lpTokens,
        'LP Token Decimals'        : lpDecimal,
        'Total LP Tokens'          : totalSupplyLP / lpDecimal,
        'Owned LP Tokens Percent'  : lpTokens * 100.0 / ( totalSupplyLP / lpDecimal ),
        'Owned Token 0'            : ( lpTokens / ( totalSupplyLP / lpDecimal ) ) * ( token0_reserve / token0Decimal),
        'Owned Token 1'            : ( lpTokens / ( totalSupplyLP / lpDecimal ) ) * ( token1_reserve / token1Decimal),
        'Total Token 0 Reserve'    : token0_reserve / token0Decimal,
        'Total Token 1 Reserve'    : token1_reserve / token1Decimal,
        'Last Block Time'          : lastblock,
        'Pair Address'             : pairAddress
    })

    return poolInfo

# Flask app starts
@app.route('/sushiswap/poolinfo', methods = ['GET'])
def sushiswap_poolinfo():
    pairAddress       = request.args.get('pa')
    lpTokens          = float(request.args.get('lp'))

    poolInfo = getPoolInfo( smartContractName = 'sushiswap_pair' ,
                            pairAddress = pairAddress , 
                            lpTokens = lpTokens )

    return poolInfo

if __name__ == '__main__':
    app.run(threaded = True)
