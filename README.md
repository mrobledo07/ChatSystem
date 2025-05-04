# SD task 1

# Summary of the project
The system that we have implemented for the realization of the project includes all the basic functionalities of a chat system. It has two main components: the client and the server.

The server is the machine that hosts the redis database (which we use as nameserver for private chats) and a rabbitmq container that runs the message broker service MOM (Message Oriented Middleware) that supports the group chat, chat discovery and insult channel functionalities.

Users can send messages to each other via private peer-to-peer chats implemented with gRPC, the fact that they are peer-to-peer implies that direct communication is being used (except for discovering the IP address and port of the other client for which they will need to query the server's redis database).
In addition, they can also subscribe to different groups and connect to them to view and send messages. In this case the communication is indirect since all the message management is handled by the rabbitmq server (a.k.a. broker).
Finally, we have the chat discovery functionality, thanks to which a client can know which users are connected at any given moment, and the insult channel, where as clients connect they can send insults that will reach only one of the clients that is connected to the channel at that moment. These two features are also based on rabbitmq.

## Execution
The system is designed to run on Linux. The execution of both the server and the client/clients is automated by means of the scripts start_server.sh and start_client.sh, which are in charge of performing the necessary configurations and initializations for the execution of the project.

Run the server: `bash start_server.sh`.
Run the client/s: `bash start_client.sh`.

## 👨‍💻 Developers

- Miguel Robledo Kusz  
- Víctor Fosch Tena

## 📚 Academic Context

This project was developed as part of the *Distributed Systems* course at the **Universitat Rovira i Virgili (URV)** in Tarragona, Spain.


