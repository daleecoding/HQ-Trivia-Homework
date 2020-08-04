# HQ-Trivia-Homework
## Purpose
This project provides a trivia game server loosely based on the popular HQ Trivia game.
## Architecture
The client and the server communicates using a websocket. 
The entire server code is written in Python3 using asyncio and websockets library.
The websockets library states that it can service 100's of connections.
Any client is expected to open a websocket connection to the server and communicate using a JSON RPC 1.0 model.

High availability can be achieved through an application load balancer. However, any existing game sessions will be lost when a server is lost.
## Rule of the Game
- Each player connects through a separate websocket connection
- When N number of players are connected and waiting, game session commences.
- Game session can have 1 or more rounds. Each round consists of:
    - Players are given the same questions
    - If the player provides an incorrect answer or does not provide an
      answer within the timeout, the player is eliminated from the game.
    - If there are two more or players left in the game, go to the next round.
      Otherwise if 1 player is remaining, that player is the winner and game ends.
      Otherwise there is no winner and the game ends.
## Design
The main entry for the package is in gamemanager module.  In GameManager.main(), websocketserver module is started and is blocked on the current event loop until it is stopped. websocketserver module notifies new websocket connections to the GameManager. GameManager maintains the list of players waiting. GameManager adds the new connection to the waiting list. If the waiting list meets the minimum number of players, a GameSession is created and is run using asyncio.await. In GameSession, the following high-level logic is implemented:
- While two or more players left in the game:
 - Generate a question
 - Send questions to the players
 - Receive an answer with timeout. If timeout, answer is None.
 - Calculate the statistics on how many players have picked each of the choices.
 - Send the answer, statistics, and the result to all players.
 - Eliminate the players who have answered incorrectly. Set the future on the players
   so that they can be unblocked from the websocketserver callback.
 - Determine winner if there's only one player left. Set the future on the winner as well.

The message exchange between the GameSession and the client is done via JSON RPC based messages. Player class provides a single point of message exchange with a websocket client. Here's an example of the JSON RPC message exchanges between the server and the client:

    JSON RPC Example in 1 round of game:

    Server to the Client
    --------------------
    - If player connects but min number of players is not met yet
    {"id": 1, "method": "announcement", "params": {"message": "Please be patient. Waiting for 2 players to join."}}
    - As soon as enough players are present, game round starts
    {"id": 2, "method": "announcement", "params": {"message": "Game round 1 starting."}}
    - Question is sent to the player
    {"id": 3, "method": "ask_question", "params": {"question": "Pok&eacute;mon Go is a location-based augmented reality game developed and published by which company?", "choices": ["Rovio", "Zynga", "Supercell", "Niantic"]}}

    Client to the Server
    --------------------
    - Answer is sent back to the server
    {"result":"Zynga","error":null,"id":0}

    Server to the Client
    --------------------
    - Answer and the stats are sent back to the player.
    {"id": 4, "method": "answers", "params": {"question": {"question": "Pok&eacute;mon Go is a location-based augmented reality game developed and published by which company?", "choices": ["Rovio", "Zynga", "Supercell", "Niantic"], "answer": "Niantic"}, "choice_counts": [0, 1, 0, 0]}}
    - If the answer was wrong or was not provided within a timeout, this is sent:
    {"id": 5, "method": "announcement", "params": {"message": "Did not receive a correct response! You have been eliminated from the game!"}}
    - Otherwise, answer was correct and this is sent:
    {"id": 5, "method": "announcement", "params": {"message": "Congratulations, you are the winner!"}}

## Testing
All tests were run using Python 3.8.5 (64-bit) on Windows 10:
- Unit tests using Python unittest (all statements covered EXCEPT __main__):
  - In repo root directory:
    - python -m unittest
    - coverage run -m unittest discover
- Manual testing using JavaScript/HTML client against the server:
  - In repo root directory:
    - python -m hqtrivia.gamemanager
    - Load htmlclient/trivia_game_client.html in Google Chrome
    - Load the same page again in a different tab to simulate a 2nd player. The default players per game is set to 2 (can be configured using config.json)
    
## WISH LIST
- Stress testing. I didn't have enough time to hammer the server to measure its performance upper bound.
- Keep all states in a cloud DB for high-availability.
- Use cookie so that web clients can rejoin the game (say if the page is accidentally reloaded).
- Chatting capabilities between players by expanding on JSON RPC.
- More fancy JavaScript/HTML client.
