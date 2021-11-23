import json, requests
from typing import OrderedDict
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
    poolInfo = OrderedDict({ "tokenLp" : {} , "token0" : {} , "token1" : {} })

    for i,tokenAddress, in enumerate([token0_address, token1_address]):
        tokenContract = web3.eth.contract( address = tokenAddress, abi = TOKEN_ABI )
        poolInfo[f'token{i}'].update( { 'symbol'     : tokenContract.functions.symbol().call() } )
        poolInfo[f'token{i}'].update( { 'decimals'   : tokenContract.functions.decimals().call() } )
    
    # Get the divisors for each token
    token0Decimal = 10 ** poolInfo['token0']['decimals']
    token1Decimal = 10 ** poolInfo['token1']['decimals']
    
    # Update block time
    poolInfo['lastblock'] = lastblock
    
    # Update output with information
    poolInfo['tokenLp'].update( { 'address'         : pairAddress } )
    poolInfo['tokenLp'].update( { 'owned'           : lpTokens } )
    poolInfo['tokenLp'].update( { 'totalSupply'     : totalSupplyLP / lpDecimal } )
    poolInfo['tokenLp'].update( { 'proportionOwned' : lpTokens / ( totalSupplyLP / lpDecimal ) } )

    poolInfo['token0'].update( { 'address'         : token0_address } )
    poolInfo['token0'].update( { 'owned'           : ( lpTokens / ( totalSupplyLP / lpDecimal ) ) * ( token0_reserve / token0Decimal) } )
    poolInfo['token0'].update( { 'totalReserve'    : token0_reserve / token0Decimal } )

    poolInfo['token1'].update( { 'address'         : token1_address } )
    poolInfo['token1'].update( { 'owned'           : ( lpTokens / ( totalSupplyLP / lpDecimal ) ) * ( token1_reserve / token1Decimal) } )
    poolInfo['token1'].update( { 'totalReserve'    : token1_reserve / token1Decimal } )

    return poolInfo

# Flask app starts
@app.route('/sushiswap/poolinfo', methods = ['GET'])
def sushiswap_poolinfo():
    pairAddress       = request.args.get('pa')
    lpTokens          = float(request.args.get('lp'))

    try:
        poolInfo = getPoolInfo( smartContractName = 'sushiswap' ,
                                pairAddress = pairAddress , 
                                lpTokens = lpTokens )
        poolInfo.update( { 'status' : 200 } )

    except Exception as e:
        poolInfo = { 'status' : 400 , 'error' : 'Check parameters, address must be a checksummed address'} 

    return poolInfo

if __name__ == '__main__':
    app.run(threaded = True)