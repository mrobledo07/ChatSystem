import os
import threading
import shutil
import redis
from time import sleep
from grpc_client import Client
from server_discovery import discover_server_ip
from group_chat import GroupChat
from chat_discovery import ChatDiscovery
from insult_channel import InsultChannel
from rabbitmq import RabbitMQ


client = None
nameserver = None
group_chat = None
chat_discovery = None
insult_channel = None 

def clear_screen():
    os.system('clear')

def print_menu():
    clear_screen()
    print("\n[1] Connect to private chat")
    print("[2] Subscribe to group chat")
    print("[3] Connect to group chat")
    print("[4] Discover chats")
    print("[5] Access insult channel")
    print("[6] Exit")

def subscribe_to_group_chat():
    global group_chat

    print("\n")
    try:
        chat_id = input("Enter group chat ID to subscribe: ")
        if group_chat.is_subscribed(chat_id):
            print(f"[!] You are already subscribed to group chat '{chat_id}'.")
            input("Press Enter to continue...")
            return
        try:
            group_chat.subscribe(chat_id)
            print(f"Subscribed to group chat '{chat_id}'")
            input("Press Enter to continue...")
        except Exception as e:
            print(f"[!] Error subscribing to group chat: {e}")
            input("Press Enter to continue...")
    except KeyboardInterrupt:
        return
     
def connect_to_group_chat():
    global group_chat

    print ("\n")
    try:
        chat_id = input("Enter group chat ID to connect: ")
        if not group_chat.is_subscribed(chat_id):
            print(f"[!] You must subscribe to group chat '{chat_id}' before connecting.")
            input("Press Enter to continue...")
            return
    except KeyboardInterrupt:
        return

    group_chat_interface(chat_id)


def group_chat_interface(chat_id):
    global group_chat
    messages = group_chat.get_messages(chat_id)
    stop_event = threading.Event()  # Event to signal stopping the thread


    def display_chat():
        clear_screen()
        print(f"Group Chat: {chat_id}\n")
        columns =  shutil.get_terminal_size().columns
        for msg in messages:
            if msg.startswith(client.username):
                print(msg.rjust(columns))
            else:
                print(msg.ljust(columns))
        print("\n\nType your message: ", end='', flush=True)

    def receive_callback(message):
        messages.append(message)
        display_chat()

    receive_thread = threading.Thread(target=group_chat.receive_messages, args=(chat_id, receive_callback, stop_event), daemon=True)
    receive_thread.start()
    display_chat()

    while True:
        try:
            message = input("")
            try:
                group_chat.send_message(chat_id, message)
                messages.append(f"{client.username}: {message}")
                display_chat()
            except Exception as e:
                print(f"[!] Error sending message: {e}")
                input("Press Enter to continue...")
        except KeyboardInterrupt:
            stop_event.set()
            return

def discover_chats():
    global chat_discovery
    responses = []

    stop_event = threading.Event()  # Event to signal stopping the threads

    def display_discovery_responses():
        clear_screen()
        print("Discovered Chats:\n")
        for response in responses:
            print(response)
        print("\n\nPress Enter to continue...")

    def handle_response(response):
        if response not in responses:
            responses.append(response)
            display_discovery_responses()

    def publish_discovery_event():
        while not stop_event.is_set():
            responses.clear()
            try:
                chat_discovery.publish_discovery_event()      
            except Exception as e:
                print(f"[!] Error publishing discovery event: {e}")
            sleep(3)
                    
    display_discovery_responses()

    # Start a thread to publish discovery event
    discovery_thread = threading.Thread(target=publish_discovery_event, daemon=True)
    discovery_thread.start()

    # Start listening for responses
    responses_thread = threading.Thread(target=chat_discovery.listen_for_responses, args=(handle_response, stop_event), daemon=True)
    responses_thread.start()

    try:
        input("")   
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        chat_discovery.stop_consuming()
        return

def access_insult_channel():
    global insult_channel
    insults = []
    stop_event = threading.Event()  # Event to signal stopping the thread

    def display_insults():
        clear_screen()
        print("Insults:\n")
        for insult in insults:
            print(insult)
        print("\n\nEnter your insult: ", end='', flush=True)

    def insult_callback(insult):
        insults.append(insult)
        display_insults()

    display_insults()

    # Start a thread to consume insults
    consume_thread = threading.Thread(target=insult_channel.consume_insults, args=(insult_callback, stop_event), daemon=True)
    consume_thread.start()

    try:
        while True:
            message = input("")
            try:
                insult_channel.publish_insult(message)
                display_insults()
            except Exception as e:
                print(f"[!] Error sending insult: {e}")
                input("Press Enter to continue...")
    except KeyboardInterrupt:
        stop_event.set()
        return

def get_input(prompt):
    try:
        return input(prompt)
    except KeyboardInterrupt:
        exit_program()

def get_username():
    global nameserver
    username = get_input("Enter your username: ")
    if not username[0].isalpha() or ' ' in username:
        raise Exception("Invalid username. The username must start with a letter and not contain spaces.")
    if nameserver.hgetall(username):
        raise Exception(f"User '{username}' already exists in the nameserver.")
    return username

def connect_to_private_chat():
    global client, nameserver
    print("\n")

    try:
        chat_id = input("Enter chat ID (username of the other user): ")
    except KeyboardInterrupt:
        return
    
    client_info = nameserver.hgetall(chat_id)
    if not client_info:
        print(f"[!] Error: User '{chat_id}' not found in the nameserver.")
        input("Press Enter to continue...")
        return

    ip_address = client_info.get("ip_address")
    port = client_info.get("port")

    try:
        client.connect(chat_id, ip_address, port)
        chat_interface(chat_id)
    except Exception as e:
        print(f"[!] Error connecting to chat: {e}")
        input("Press Enter to continue...")
        return

def chat_interface(chat_id):
    global client
    clear_screen()
    error = False

    # Messages list to keep track of messages
    messages = client.get_messages(chat_id)
    new_messages_event = threading.Event()  # Event to signal new messages
    new_messages_event.set()  # Signal that there are new messages
    stop_event = threading.Event()  # Event to signal stopping the threads

    def refresh_messages():
        while not stop_event.is_set():
            client.get_new_message(chat_id)
            new_messages_event.set()  # Signal that there are new messages

    def display_chat():
        while not stop_event.is_set():
            new_messages_event.wait()  # Wait for new messages
            clear_screen()
            print(f"Chat with {chat_id}\n")
            columns =  shutil.get_terminal_size().columns
            for msg in messages:
                if msg.startswith(client.username):
                    print(msg.rjust(columns))
                else:
                    print(msg.ljust(columns))
            print("\n\nType your message: ", end='', flush=True)
            new_messages_event.clear()  # Clear the event

    # Start the thread to refresh messages
    refresh_thread = threading.Thread(target=refresh_messages, daemon=True)
    refresh_thread.start()
    display_thread = threading.Thread(target=display_chat, daemon=True)
    display_thread.start()

    
    while True:
        try:
            message = input("")
            try:
                client.add_message(client.username, chat_id, message)
                new_messages_event.set()  # Signal that there are new messages
            except Exception as e:
                error = True
                print(f"[!] Error sending message: {e}")
                input("Press Enter to continue...")
        except KeyboardInterrupt:
            if error:
                client.clear_chat(chat_id)
            stop_event.set()
            new_messages_event.set()  
            return
    

def exit_program():
    global client, group_chat
    if client:
        client.close()              # Delete user from the nameserver 
    if group_chat:
        group_chat.delete_queues()  # Delete user subscriptions at exit
    print("\n\nExiting program...")
    exit(0)

def main():
    global client, nameserver, group_chat, chat_discovery, insult_channel

    clear_screen()

    print("[+] Welcome to the chat application!")
    print("\n\n\tConnecting to the nameserver...")
    sleep(1)
    server_ip = discover_server_ip()    # This will block until the server is found
    nameserver = redis.Redis(host=server_ip, port=6379, decode_responses=True)
    clear_screen()
    print("[+] Connected to the nameserver successfully!")
    print("\n\n\tStarting the chat application...")
    sleep(1)

    clear_screen()
    # While loop to get a correct username
    while True:
        try:
            username = get_username()
            client = Client(username, nameserver)
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")
            input("Press Enter to continue...")
            clear_screen()

    clear_screen()
    # While loop to handle connection errors
    while True:
        try:
            try:
                rabbitmq = RabbitMQ(username, server_ip)
                group_chat = GroupChat(rabbitmq)
                chat_discovery = ChatDiscovery(rabbitmq)
                insult_channel = InsultChannel(rabbitmq)
                break
            except Exception as e:
                print(f"[!] Error: {e}")
                print("\nRetrying in 3 seconds...")
                sleep(3)
                clear_screen()
        except KeyboardInterrupt:
            exit_program()

    menu_options = {
        1: connect_to_private_chat,
        2: subscribe_to_group_chat,
        3: connect_to_group_chat,
        4: discover_chats,
        5: access_insult_channel,
        6: exit_program
    }

    while True:
        clear_screen()
        print_menu()
        choice = get_input("\n[+] Enter your choice: ")
        if choice.isdigit() and int(choice) in menu_options:
            menu_options[int(choice)]()
        else:
            print("\n[!] Invalid choice. Please enter a number between 1 and 5.")
            get_input("Press Enter to continue...")

if __name__ == "__main__":
    main()
