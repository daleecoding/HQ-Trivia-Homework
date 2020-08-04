import asyncio
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed
from typing import List

from .question import Question


class Player:
    """
    This represents a handle to a single remote player.

    The purpose of this class is to wrap the websocket calls so that the
    GameSession class can have a bi-directional communication without
    worrying about the protocol nor the low-level communication errors.

    Future object is used to signal that game is complete for the user.
    """

    def __init__(self, future: asyncio.Future, websocket: websockets.WebSocketServerProtocol):
        self.next_json_rcp_request_id = 1
        self.future = future
        self.websocket = websocket

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"Player: [remote={self.websocket.remote_address if not None else None}]"

    async def send_question(self, question: Question):
        """Send the question to the player in a JSON RCP request format
        """

        # Take out the answer first
        params = question.__dict__.copy()
        del params['answer']

        await self.send_json_rpc_request('ask_question', params)

    async def send_answers(self, question: Question, counts: List[int]):
        """Send the question to the player in a JSON RCP request format
        """

        params = dict()
        params['question'] = question.__dict__
        params['choice_counts'] = counts

        await self.send_json_rpc_request('answers', params)

    async def send_announcement(self, message: str):
        """Send an announcement message to the player in a JSON RCP request format
        """

        # Take out the answer first
        params = dict()
        params['message'] = message

        await self.send_json_rpc_request('announcement', params)

    async def recv_answer(self):
        """Receive the result that contains just an answer
        """

        # Keep it simple for now and only care about the result.
        (request_id, error, result) = await self.receive_json_rpc_response()

        return result

    async def send_json_rpc_request(self, method: str, params: dict):
        """Returns JSON text from the method and params provided.
        Loosely following https://www.jsonrpc.org/ Version 1.0 for the request format.
        """
        root = dict()
        root['id'] = self.next_json_rcp_request_id
        self.next_json_rcp_request_id += 1

        root['method'] = method
        root['params'] = params
        json_string = json.dumps(root)

        try:
            await self.websocket.send(json_string)
        except ConnectionClosed as e:
            logging.warning(
                "Connection closed while trying to send(): %s", e)
        # TypeError can be raised but that would be a bug on our part in
        # trying to send different types of data, and we want that to
        # propagate to the user

    async def receive_json_rpc_response(self) -> (int, str, str):
        """Returns id, result, and error from JSON RPC response.
        Loosely following https://www.jsonrpc.org/ Version 1.0 for the response format.

        Returns
        -------
        (id, error, result) if JSON successfully parsed. Otherwise (None, None, None).
        """
        json_string = (None, None, None)

        try:
            json_string = await self.websocket.recv()
        except ConnectionClosed as e:
            logging.warning(
                "Connection closed while waiting for recv(): %s", e)
            # Set json string to None. It should cause exception below and return (None, None, None).
            json_string = None
        # RuntimeError can be raised if two coroutines call recv() concurrently.
        # That would be a bug and we want that to propagate to the user.

        try:
            response = json.loads(json_string)
            return (response['id'], response['error'], response['result'])
        except:
            return (None, None, None)
