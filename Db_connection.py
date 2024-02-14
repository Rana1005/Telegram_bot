# demo.py
import schedule
import time
from pymongo import MongoClient

client = MongoClient('mongodb+srv://pratappatil:Mobiloitte1@cluster0.l1qs6zy.mongodb.net/')
db = client.JoshwaDB
chatid_collection = db.chat_id
thread_collection = db.thread_dict

# data ={}
# data2 ={}
def push_chatid(chatId_dict):
    print("inside function")
    # # Your logic for creating Chat ID
    # chatid_data = chatId_dict
    # print("/////chatid data",chatid_data)
    # # Upload data to Chatid collection
    # chatid_collection.insert_one(chatid_data)
    existing_data = chatid_collection.find_one(chatId_dict)
    print("Existing Data", existing_data)

    if existing_data:
        print(f"Chat ID {chatId_dict} already exists in the collection. Skipping.")
        
    else:
        print(f"Chat ID {chatId_dict} does not exist. Pushing to collection.")
        print(chatid_collection, "Chat ID COllection")
        chatid_collection.insert_one(chatId_dict)

# Schedule the job to run every 0.5 minutes for demonstration purposes
# def get_chatid(chatId_dict):
#     print("\n\nget_chatid called",chatId_dict)
#     schedule.every(0.01).minutes.do(create_chatid(chatId_dict))

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
