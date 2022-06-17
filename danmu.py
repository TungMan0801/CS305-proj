import asyncio
import websockets
import json
connected = []
old_comments=[]
old_users=[]
IP_ADDR = "0.0.0.0"
IP_PORT = "8765"

async def ServerEcho(websocket):
    print("new client entered.")
    connected.append(websocket)
    await websocket.send(json.dumps({"Type":"history","Text":old_comments,"User":old_users}))

    
    try:
     while True:
        recv_text = await websocket.recv()
        print("recv:", recv_text)
        recv_dict=json.loads(recv_text)
        if(recv_dict["Type"]=="danmu"):
         if len(connected)>0:
            for connetion in connected:
                    await connetion.send(json.dumps({"Type":"danmu","Text":recv_dict["Text"]}))
        elif(recv_dict["Type"]=="comment"):
           old_comments.append(recv_dict["Text"])
           old_users.append(recv_dict["User"])
           if len(connected)>0:
            for connetion in connected:
                    await connetion.send(json.dumps({"Type":"comment","Text":recv_dict["Text"],"User":recv_dict["User"]}))
   
    except websockets.exceptions.ConnectionClosedOK:
        print("A client has exited")
 
    finally:
            connected.remove(websocket)
            await websocket.close()
            
 
async def serverRun(websocket, path):
    
    if path=='/':
        await ServerEcho(websocket)

        
server = websockets.serve(serverRun, IP_ADDR, IP_PORT)
asyncio.get_event_loop().run_until_complete(server)
asyncio.get_event_loop().run_forever()