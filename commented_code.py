# import eventlet
# eventlet.wsgi.server(eventlet.listen(('localhost', 8000)), app)

# import websockets

# loop = None

# async def start_loop():
#     global loop
#     while True:
#         # Your asyncio-based logic to generate data
#         data = ...

#         # Send data to the connected client(s)
#         await asyncio.gather(*[ws.send(data) for ws in connected_clients])

# async def handle_command(websocket, command):
#     global loop
#     if command == "start":
#         if loop is None:
#             loop = asyncio.create_task(start_loop())
#     elif command == "stop":
#         if loop is not None:
#             loop.cancel()
#             loop = None

# connected_clients = set()

# async def websocket_handler(websocket, path):
#     connected_clients.add(websocket)
#     try:
#         async for message in websocket:
#             await handle_command(websocket, message)
#     finally:
#         connected_clients.remove(websocket)

# asyncio.get_event_loop().run_until_complete(
#     websockets.serve(websocket_handler, '0.0.0.0', 8765))
# asyncio.get_event_loop().run_forever()
# start_server = websockets.serve(echo, "localhost", 8765)
# asyncio.get_event_loop().run_until_complete(start_server)
# asyncio.get_event_loop().run_forever()
# socketio_thread_local.socketio = socketIO
# socketio.run(app)


# @app.route('/start', methods=['GET'])
# async def start_bot():
 
#     try:    
#         print("here")
#         
#         print("jere")
#         
#         await listenForTokens(lastRunTime)
#         print("mere")
#         return jsonify({'message': 'Token sniper bot started successfully'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/wallet', methods=['GET'])
# def return_wallet_details():
#     # Your token sniper bot logic here
#     global walletAddress
#     global private_key
#     private_key = os.urandom(32).hex()

# # Derive the wallet address from the private key
#     account = web3.eth.account.privateKeyToAccount(private_key)
#     walletAddress = account.address

#     return jsonify({'walletAddress': walletAddress, 'privateKey':private_key}), 200


# if __name__ == '__main__':
#     print("up and running at port 5000")
#     app.run(host='0.0.0.0', port=5000)



